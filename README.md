This game is a simple one where each player repeatedly presses the left and right button to see who can do the most in 10 seconds. 

How to run the game in multiplayer:

    1. On server computer (host), find its IP using ipconfig. then run the docker commands.
    2. Then run 'python spam_game_online.py' then enter the server IP.
    2. On player computer (guest), you run 'python spam_game_online.py' then enter the host's IP address.
    3. Open game tab and enjoy the game.


Docker commands for host:

    docker build -t spam-server -f Dockerfile.server .
    docker run -d -p 5000:5000 --name spam-server-container spam-server
    python spam_game_online.py
    Enter server IP: 127.0.0.1

For player that is joining:

    python spam_game_online.py
    Enter server IP: (IP OF HOST FROM IPCONFIG)
