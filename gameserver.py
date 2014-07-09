#!/usr/bin/env python
#title           :gameserver.py
#description     :game server
#author          :Moises Holguin
#date            :10-23-2013
#python_version  :2.7.3
#==============================================================================
import socket
from connect4  import Connect4
from msgproxy  import MsgProxy
from threading import Thread
from pprint    import pprint as pp

# Represent a player
class Player(object):
  def __init__(self, player_id, player_name, player_socket):
    self.id = player_id
    self.name = player_name
    self.socket = player_socket

# Global Variables
msg = MsgProxy()
games = {}
next_game_id = 0
HOST = socket.gethostname()
PORT = 1025
TIMEOUT = 5
GAMES = {'Connect4': Connect4}
MSG_FORMATS = {'GAMES': '("GAMES",)', 
               'OPPONENTS': '("OPPONENTS",)', 
               'REQUEST': '("REQUEST", str(game_name), int(player_id:1 or 2), str(player_name))\n' + 
                          '("REQUEST", int(game_id), int(player_id:1 or 2), str(player_name))'}

if __name__ == '__main__':
  try:
    # Create main socket
    passive_socket = socket.socket()
    passive_socket.bind((HOST, PORT))
    passive_socket.listen(100)
    print 'main socket on port', PORT
    # Main client-request handling loop
    socket.setdefaulttimeout(TIMEOUT)
    while passive_socket:
      try:
        keep_player_socket = False
        msg.clear()
        print 'Waiting for connection'
        # Wait for a client to connect and send a message
        player_socket, addr = passive_socket.accept()
        print 'Got connection from', addr
        request = msg.recv(player_socket)
        print 'From connection', addr, 'received:', request
        if not (request and type(request) is tuple and request[0] in MSG_FORMATS):
          print 'Bad message format, or a timeout occurred'
          response = ('After connect returns, you have {0} seconds to send one of these message tuples:\n' +
                      '\n'.join(MSG_FORMATS.values()) + '\n' + 'via an instance of MsgProxy').format(TIMEOUT)
        else:
          # Handle the message
          if request[0] == 'GAMES':
            response = GAMES.keys()
          elif request[0] == 'OPPONENTS':
            # Send the client a list of games awaiting opponents
            response = []
            for gid, (game_thread, p1, p2, gname) in games.items():
              pp((gid, (game_thread, p1, p2, gname)))
              if (not isinstance(game_thread, Thread)) or (not game_thread.is_alive()):
                print 'Removing game (%d): %s, %s Vs %s' % (gid, gname, p1, p2)
                del games[gid]
              else:
                if not (p1 and p2):
                  response.append((gid, p1, p2, gname))
          elif request[0] == 'REQUEST':
            # Client is asking to play in a game
            game_id, player_id, player_name = request[1:]
            assert player_name is not None, 'None object cannot be used as player name.'
            if type(game_id) is str:
              # Client is requesting a new game instance so create and start one
              game_thread = GAMES[game_id]()
              game_data = [game_thread, None, None, game_id]
              game_data[player_id] = player_name
              games[next_game_id] = game_data
              next_game_id += 1
              game_thread.start()
              response = keep_player_socket = True
            else:
              # Client is requesting to join an existing game instance
              if game_id in games and None in games[game_id]:
                # It is still possible to join the requested game
                game_thread = games[game_id][0]
                player_id = games[game_id].index(None)
                games[game_id][player_id] = player_name
                response = keep_player_socket = True
              else:
                # It is not possible to join the requested game
                response = keep_player_socket = False
      except KeyboardInterrupt as e:
        # Catch when the user hits CTRL + C
        print '\nUser terminated program'
      except BaseException as e:
        response = ('ERROR', e.__class__.__name__, e.args)
      finally:
        if player_socket:
          print 'Sending response: ', response
          if msg.send(player_socket, response) and keep_player_socket:
            # Pass a player object to the game thread
            player_socket.settimeout(None)
            p = Player(player_id, player_name, player_socket)
            game_thread.send(p)
          else:
            player_socket.close()
  except KeyboardInterrupt as e:
    # Catch when the user hits CTRL + C
    print '\nUser terminated program'
  except BaseException as e:
    # Catch any unexpected error
    print '\nAn unexpected error has occurred:'
    print e.__class__.__name__, e.args
  finally:
    # Always close open sockets and exit gracefully
    passive_socket.close()
    for (game_thread, p1, p2) in games.values():
      game_thread.close()
    print 'Exiting Connect4 Server Program'
    print 'Goodbye'
