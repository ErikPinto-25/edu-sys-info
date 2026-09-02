"""Educational system information viewer with explicit sharing consent."""

from __future__ import annotations

import os
import socket
import threading
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
import tkinter as tk
from tkinter import messagebox, ttk


APP_NAME = "Edu Sys Info"
PUBLIC_IP_SERVICE = "https://api.ipify.org"
REQUEST_TIMEOUT_SECONDS = 7
WEBHOOK_ENV_VAR = "EDU_SYS_INFO_WEBHOOK_URL"
DISCORD_WEBHOOK_HOSTS = {
    "discord.com",
    "discordapp.com",
    "canary.discord.com",
    "ptb.discord.com",
}


@dataclass(frozen=True)
class SystemInfo:
    """The small, documented set of values collected by this application."""

    hostname: str
    local_ip: str
    public_ip: str

    def as_text(self) -> str:
        return (
            "Collection completed\n\n"
            f"Hostname: {self.hostname}\n"
            f"Local IP: {self.local_ip}\n"
            f"Public IP: {self.public_ip}"
        )


def get_local_ip() -> str:
    """Return the IPv4 address used by the active network interface."""

    try:
        # UDP connect selects an interface but does not transmit application data.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.connect(("1.1.1.1", 80))
            return udp_socket.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "Unavailable"


def get_public_ip(http_client=requests) -> str:
    """Query the documented public-IP service, handling network failures."""

    try:
        response = http_client.get(
            PUBLIC_IP_SERVICE,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": "edu-sys-info/1.0"},
        )
        response.raise_for_status()
        return response.text.strip() or "Unavailable"
    except requests.RequestException:
        return "Unavailable"


def collect_system_info(http_client=requests) -> SystemInfo:
    """Collect only the values displayed in the interface."""

    return SystemInfo(
        hostname=socket.gethostname(),
        local_ip=get_local_ip(),
        public_ip=get_public_ip(http_client),
    )


def is_valid_discord_webhook(url: str) -> bool:
    """Accept only HTTPS Discord webhook URLs with an id and token."""

    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False

    path_parts = [part for part in parsed.path.split("/") if part]
    return (
        parsed.scheme == "https"
        and parsed.hostname in DISCORD_WEBHOOK_HOSTS
        and len(path_parts) >= 4
        and path_parts[:2] == ["api", "webhooks"]
        and bool(path_parts[2])
        and bool(path_parts[3])
    )


def send_to_discord(webhook_url: str, info: SystemInfo, http_client=requests) -> None:
    """Send exactly the information already shown to the consenting user."""

    if not is_valid_discord_webhook(webhook_url):
        raise ValueError("Enter a valid HTTPS Discord webhook URL.")

    response = http_client.post(
        webhook_url.strip(),
        json={
            "content": info.as_text(),
            "allowed_mentions": {"parse": []},
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": "edu-sys-info/1.0"},
    )
    response.raise_for_status()


class EduSysInfoApp:
    """Tkinter interface that separates local collection from remote sharing."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.last_info: SystemInfo | None = None
        self.busy = False

        self.webhook_var = tk.StringVar(value=os.getenv(WEBHOOK_ENV_VAR, ""))
        self.consent_var = tk.BooleanVar(value=False)
        self.show_webhook_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready. Nothing has been collected or sent.")

        self._configure_window()
        self._build_interface()
        self.webhook_var.trace_add("write", self._on_form_change)

    def _configure_window(self) -> None:
        self.root.title(APP_NAME)
        self.root.geometry("680x560")
        self.root.minsize(620, 520)
        self.root.option_add("*Font", ("Segoe UI", 10))

    def _build_interface(self) -> None:
        container = ttk.Frame(self.root, padding=24)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(
            container,
            text="Educational System Information",
            font=("Segoe UI", 18, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            container,
            text=(
                "This application collects only the hostname, local IP and public IP. "
                "Collection is displayed locally first; sending is always a separate action."
            ),
            wraplength=610,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", pady=(8, 18))

        self.collect_button = ttk.Button(
            container,
            text="Collect and display locally",
            command=self._collect,
        )
        self.collect_button.grid(row=2, column=0, sticky="w")

        result_frame = ttk.LabelFrame(container, text="Collected data", padding=10)
        result_frame.grid(row=4, column=0, sticky="nsew", pady=16)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.result_text = tk.Text(
            result_frame,
            height=9,
            wrap="word",
            state="disabled",
            background="#f5f5f5",
            relief="flat",
            padx=10,
            pady=10,
        )
        self.result_text.grid(row=0, column=0, sticky="nsew")

        share_frame = ttk.LabelFrame(container, text="Optional Discord sharing", padding=12)
        share_frame.grid(row=5, column=0, sticky="ew")
        share_frame.columnconfigure(0, weight=1)

        ttk.Label(share_frame, text="Discord webhook URL:").grid(
            row=0, column=0, sticky="w"
        )
        self.webhook_entry = ttk.Entry(
            share_frame,
            textvariable=self.webhook_var,
            show="•",
        )
        self.webhook_entry.grid(row=1, column=0, sticky="ew", pady=(4, 6))

        ttk.Checkbutton(
            share_frame,
            text="Show webhook URL",
            variable=self.show_webhook_var,
            command=self._toggle_webhook_visibility,
        ).grid(row=2, column=0, sticky="w")

        ttk.Checkbutton(
            share_frame,
            text=(
                "I own or am authorized to use this computer and consent to sending "
                "the displayed data."
            ),
            variable=self.consent_var,
            command=self._update_send_button,
        ).grid(row=3, column=0, sticky="w", pady=(8, 8))

        self.send_button = ttk.Button(
            share_frame,
            text="Send displayed data to Discord",
            command=self._send,
            state="disabled",
        )
        self.send_button.grid(row=4, column=0, sticky="w")

        ttk.Label(
            container,
            textvariable=self.status_var,
            foreground="#3a3a3a",
            wraplength=610,
        ).grid(row=6, column=0, sticky="ew", pady=(14, 0))

    def _on_form_change(self, *_args: object) -> None:
        self._update_send_button()

    def _toggle_webhook_visibility(self) -> None:
        self.webhook_entry.configure(show="" if self.show_webhook_var.get() else "•")

    def _update_send_button(self) -> None:
        can_send = (
            not self.busy
            and self.last_info is not None
            and self.consent_var.get()
            and bool(self.webhook_var.get().strip())
        )
        self.send_button.configure(state="normal" if can_send else "disabled")

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        self.collect_button.configure(state="disabled" if busy else "normal")
        self._update_send_button()

    def _show_result(self, text: str) -> None:
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.configure(state="disabled")

    def _run_background(self, task, on_success, working_status: str) -> None:
        self._set_busy(True)
        self.status_var.set(working_status)

        def worker() -> None:
            try:
                result = task()
            except (requests.RequestException, ValueError, OSError) as error:
                error_message = str(error) or error.__class__.__name__
                self.root.after(0, lambda: self._handle_error(error_message))
            else:
                self.root.after(0, lambda: on_success(result))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_error(self, error_message: str) -> None:
        self._set_busy(False)
        self.status_var.set("Operation failed. No data was sent.")
        messagebox.showerror("Operation failed", error_message)

    def _collect(self) -> None:
        self._run_background(
            task=collect_system_info,
            on_success=self._collection_finished,
            working_status="Collecting the documented values...",
        )

    def _collection_finished(self, info: SystemInfo) -> None:
        self.last_info = info
        self._show_result(info.as_text())
        self._set_busy(False)
        self.status_var.set("Collection complete. Nothing has been sent.")

    def _send(self) -> None:
        if self.last_info is None:
            messagebox.showwarning("Collect first", "Collect and review the data first.")
            return

        if not self.consent_var.get():
            messagebox.showwarning("Consent required", "Confirm consent before sending.")
            return

        webhook_url = self.webhook_var.get().strip()
        if not is_valid_discord_webhook(webhook_url):
            messagebox.showerror(
                "Invalid webhook",
                "Enter a valid HTTPS Discord webhook URL.",
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm sending",
            "Send exactly the data currently displayed to this Discord webhook?",
        )
        if not confirmed:
            self.status_var.set("Sending cancelled. No data was sent.")
            return

        info_to_send = self.last_info
        self._run_background(
            task=lambda: send_to_discord(webhook_url, info_to_send),
            on_success=lambda _result: self._sending_finished(),
            working_status="Sending the displayed data...",
        )

    def _sending_finished(self) -> None:
        self._set_busy(False)
        self.status_var.set("The displayed data was sent successfully.")
        messagebox.showinfo("Success", "The displayed data was sent to Discord.")


def main() -> None:
    root = tk.Tk()
    EduSysInfoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
