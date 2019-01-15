import paho.mqtt.client as mqtt
import tkinter
from tkinter import messagebox
import configparser
from sys import exit
from time import sleep


config=configparser.ConfigParser()
try:
    config_data = config.read('config.ini')
    mqtt_server_IP = config['MQTT']['ServerIP']
    mqtt_server_port = int(config['MQTT']['ServerPort'])
    pub_topic = config['MQTT']['PubTopic']
    sub_topic = config['MQTT']['SubTopic']
    user = config['MQTT']['User']
    passwd = config['MQTT']['Password']
except (KeyError, NameError) as err:
    if not config_data:
        msg = "Configuration file missing"
    else:
        msg = "Configuration file error: "+str(err)+" cannot be found"
    messagebox.showerror("Error", msg )
    exit()


pwr_msg=''


# The callback for when the client receives a CONNACK response from the server.
connack_rc=['',
            "Connection Refused, unacceptable protocol version",
            "Connection Refused, identifier rejected",
            "Connection Refused, Server unavailable",
            "Connection Refused, bad user name or password",
            "Connection Refused, not authorized"]


def on_connect(client, userdata, flags, rc):
    if rc > 0:
        try:
            messagebox.showerror("Error", connack_rc)
        except IndexError:
            messagebox.showerror("Error", "Connection Refused, Invalid Connect return code")
        finally:
            exit()


def on_message(__client, __userdata, msg ):
     global pwr_msg
     msgstr = (str(msg.payload)[2:-1])
     if not msgstr.startswith('{'):
         pwr_msg = msgstr


def send_message(client, msg, btn_txt, statusLabel,status_txt ):
    client.publish(pub_topic, 'TOGGLE')
    btn_txt.set(msg)
    not_msg='On' if msg == 'OFF' else 'Off'
    col = 'red' if not_msg == 'Off' else 'green'
    status_txt.set('The Printer Is Currently '+not_msg)
    statusLabel.config(fg=col)


def quit_program(client):
    client.loop_stop()
    client.disconnect()
#    print("Closed connection")
    exit()


def main():
    global pwr_msg
    ini =True

    try:
        client = mqtt.Client()
        client.username_pw_set(username=user, password=passwd)
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(mqtt_server_IP, mqtt_server_port)
    except OSError:
        messagebox.showerror("Error", "Failed to connect to MQTT server on " + mqtt_server_IP)
        exit()
    client.publish(pub_topic)
    client.subscribe(sub_topic)
    client.loop_start()

    # Wait for status from switch
    wait_ct=0
    while pwr_msg=='':
        sleep(0.1)
        wait_ct+=1
        if wait_ct>19:
            messagebox.showerror("Error", "Timeout getting initial status of the switch.")
            exit()
    if ini:  # and toggle the first status
        ini = not ini
        txt_msg='ON' if pwr_msg=='OFF' else 'OFF'

    # Build TKinter frame
    root = tkinter.Tk()
    root.title("Printer Status")
    root.geometry("250x100+30+30")
    root["padx"] = 20
    root["pady"] = 20

    main_frame = tkinter.Frame(root, relief='raised')
    main_frame.grid()

    status_txt=tkinter.StringVar()
    status_txt.set("The Printer is currently "+pwr_msg.title())

    statusLabel = tkinter.Label(main_frame, textvariable=status_txt)
    statusLabel.grid(row=0)
    col = 'red' if pwr_msg == 'OFF' else 'green'
    statusLabel.config(fg=col)

    fntryLabel = tkinter.Label(main_frame)
    fntryLabel["text"] = ""
    fntryLabel.grid(row=1)

    btn_txt=tkinter.StringVar()
    btn_txt.set(txt_msg)
    msg_button = tkinter.Button(main_frame, width=6, textvariable=btn_txt)

    msg_button.grid(row=2, column=0)
    msg_button['command'] = lambda: send_message(client, pwr_msg, btn_txt, statusLabel, status_txt)
    # root.bind('<Return>', lambda event: send_message(client, pwr_msg))

    q_button = tkinter.Button(main_frame, text="Quit")
    q_button.grid(row=2, column=4)
    q_button['command'] = lambda: quit_program(client)

    root.mainloop()


main()
