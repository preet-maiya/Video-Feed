from Server import SendVideo, GetCommands


video_quality = 60
host = "127.0.0.1"
video_port = 1080
control_port = 1081
command_port = 1000

sender = SendVideo(host, video_port, control_port, video_quality)
receiver = GetCommands(host, command_port)

sender.start()
receiver.start()
