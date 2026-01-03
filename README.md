# Battle ship

```
 ___       _   _   _          _    _        _ _ _ 
| _ ) __ _| |_| |_| |___   __| |_ (_)_ __  | | | |
| _ \/ _` |  _|  _| / -_) (_-< ' \| | '_ \ |_|_|_|
|___/\__,_|\__|\__|_\___| /__/_||_|_| .__/ (_|_|_)
                                    |_|           
```

--------------------------------------------------------------------------------------- 

#Connect server (if you use server and client on different platforms) 

1. Open PORT from WSL to Window Interface 

2. Run this code (while turn of firewall) 

netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0  

connectport=8080 connectaddress=172.29.188.129 

--------------------------------------------------------------------------------------- 

How to start 

1. Start server (ubuntu/wsl/linux) 

cd server/src 


gcc server.c database.c game.c response.c utils.c cJson.c -o server  

-lsqlite3 -lssl -lcrypto -lpthread -lm 


./server 


2. Start client 

cd UI\battle_ship 

python -m venv venv 

Venv\Scripts\activate 

pip install -r requirements.txt 

cd src 

python main.py 

 

--------------------------------------------------------------------------------------- 

 

 