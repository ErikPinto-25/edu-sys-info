import socket
import requests
import tkinter as tk
from tkinter import messagebox

# Educational purpose only.
# Do not use without user consent.
# This code collects system information and sends it to a Discord webhook.
# Ensure you have permission to run this code on the target system.
# Im not responsible for any misuse of this code.

#Hostname, IP-L, IP-P collection function
def data_colection():
    hostname = socket.gethostname()
    ip_local = socket.gethostbyname(hostname)
    try:
        ip_publico = requests.get("https://api.ipify.org", timeout=5).text
    except:
        ip_publico = "not found"

#Mensage in Webhook bot Discord and Tkinter window interface 
    return f"""
**Collection done**

Hostname: {hostname}
IP-L: {ip_local}
IP-P: {ip_publico}
"""

#Webhook configuration and sending function
def send_webhook_message(data): 
    WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
    payload = {
        "content": data_colection()}
    response = requests.post(WEBHOOK_URL, json=payload)
    print("Status code is:", response.status_code)
    print("Response is:", response.text)

def execute():
    data = data_colection()
    text_result.config(state="normal")
    text_result.delete("1.0", tk.END)
    text_result.insert(tk.END, data)
    text_result.config(state="disabled")

    send_webhook_message(data)
    messagebox.showinfo("Success", "Data collected and sent via webhook!")

#Interface and Tkinter setup
window = tk.Tk()
window.title("Data Collector")
btn_collect = tk.Button(window, text="If you click the button, your data will be sent to Discord webhook", command=execute)
btn_collect.pack(pady=10)
text_result = tk.Text(window, height=10, width=50, state="disabled")
text_result.pack(pady=10)
window.mainloop()