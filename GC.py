import sys
import socket
from msgproxy import MsgProxy

def get_user_input(message, err_msg, validate):
    while True:
        ip = raw_input(message)
        if validate(ip): break
        print err_msg
    return ip

def request_game(game_id, player_id):
    connect()
    msg.send(player_socket, ('REQUEST', game_id, player_id, player_name))
    success = msg.recv(player_socket)
    if not success:
        print 'Request denied by server'
        player_socket.close()
        return False
    return True

def play_game(player_id):
    get_game_message()
    first_move = True
    while True:
        if not (first_move and player_id == 2):
            assert msg.send(player_socket, raw_input('Enter your move: ')), 'Lost communications with the GameServer.'
            message = get_game_message()
            if 'INVALID MOVE' in message: continue
            if 'GAME OVER' in message: break
        if first_move: first_move = False
        print 'Waiting for your opponent to move...'
        message = get_game_message()
        if 'GAME OVER' in message: break
    player_socket.close()

def get_game_message():
    message = msg.recv(player_socket)
    assert message, 'Lost communications with the GameServer.'
    print message
    return message

def get_game_names():
    connect()
    msg.send(player_socket, ('GAMES',))
    game_names = msg.recv(player_socket)
    player_socket.close()
    return game_names

def connect():
    global player_socket
    player_socket = socket.socket()
    player_socket.connect((HOST, PORT))

# GLOBALS
msg = MsgProxy()
player_socket = None
PORT = 1025
HOST = socket.gethostname()

# MAIN
if __name__ == '__main__':
    if len(sys.argv) > 1: HOST = sys.argv[1]
    player_name = get_user_input('Enter your name: ', 'Name cannot be blank.', lambda ip: ip.replace(' ', '') != '')

    try:
        game_names = get_game_names()
        while True:
            connect()
            msg.send(player_socket, ('OPPONENTS',))
            opponents = msg.recv(player_socket)
            player_socket.close()
            if opponents == []:
                print 'No games are awaiting players'
            else:
                for i, (game_id, p1, p2, game_name) in enumerate(opponents):
                    game_str = '({0}): {1}, {2} Vs {3}'
                    print game_str.format(i, game_name, p1, p2)
            print '(r): refresh the list of games awaiting players'
            print '(n): start a new game'
            print '(q): quit'
            choice = get_user_input('Enter your choice: ', 'You must enter one of the numbers or letters in paren.', lambda ip: (ip in ('r', 'n', 'q')) or (ip.isdigit() and 0 <= int(ip) < len(opponents)))
            if choice == 'r': continue
            elif choice == 'q': break
            elif choice == 'n':
                for i, game_name in enumerate(game_names):
                    print '({0}): {1}'.format(i, game_name)
                game_choice = int(get_user_input('Which game would you like to play?', 'You must enter one of the numbers in paren.', lambda ip: ip.isdigit() and 0 <= int(ip) < len(game_names)))
                game_id = game_names[game_choice]
                player_id = int(get_user_input('Choose player(1) or player(2): ', 'You must enter 1 or 2.', lambda ip: ip in ('1', '2')))
                if request_game(game_id, player_id):
                    print 'Waiting for an opponent to join the game...'
                    play_game(player_id)
            else:
                choice = int(choice)
                game_id = opponents[choice][0]
                player_id = opponents[choice].index(None)
                if request_game(game_id, player_id):
                    play_game(player_id)

    except KeyboardInterrupt as e:
        print '\nUser terminated program.'

    except BaseException as e:
        print '\nAn unexpected error has occurred:'
        print e.__class__.__name__, e.args

    finally:
        if player_socket: player_socket.close()
        print 'Exiting Game Client Program.'
        print 'Goodbye.'
