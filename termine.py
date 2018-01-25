#!/usr/bin/python
# -*- coding: utf-8 -*-

# termine, a terminal minesweeper clone
# Copyright (C) 2017  Damien Picard dam.pic AT free.fr
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import argparse
import re
import sys
import os
import random
import time

# var init
ROWS = 'abcdefghjklmnopqrstuvwxyz'
width = 8
height = 8
mines = 10
grid = []
current_coords = [0, 0]
start_time = time.time()
game_ended = False
first_move = True


# from http://stackoverflow.com/a/21659588
# input getter
def _find_getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys
    import tty

    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch


getch = _find_getch()

class Cell(object):

    TEXTS = {
        0: 'o',
        1: '1',
        2: '2',
        3: '3',
        4: '4',
        5: '5',
        6: '6',
        7: '7',
        8: '8',
        'F': u'F',
    }

    def __init__(self, coords, grid, is_mine):
        self.grid = grid
        self.coords = coords
        self.is_mine = is_mine
        self.is_flagged = False
        self.is_opened = False

    def compute_adjacent(self):
        global grid
        self.adjacent = 0
        if self.is_mine:
            return
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                x = dx + self.coords[0]
                y = dy + self.coords[1]
                if x < 0 or y < 0 or x >= width or y >= height:
                    continue
                if grid[x][y].is_mine:
                    self.adjacent += 1

    def get_output(self):
        output = ' '
        if self.is_opened:
            if self.is_mine:
                output = u'\u2737'
            else:
                output = self.TEXTS[self.adjacent]
        elif self.is_flagged:
            output = self.TEXTS['F']
        return output

    def toggle_flag(self):
        self.is_flagged = not self.is_flagged


def generate_grid(width, height, mines):
    grid = []
    mines = [True if (n < mines) else False for n in range(width*height)]
    random.shuffle(mines)
    for x in range(width):
        row = []
        for y in range(height):
            row.append(Cell((x, y), grid, mines[y*width+x]))
        grid.append(row)
    return grid


def compute_grid():
    global grid
    for x in range(width):
        for y in range(height):
            grid[x][y].compute_adjacent()


def flag():
    coords = current_coords
    cell = grid[coords[0]][coords[1]]
    if not cell.is_opened:
        cell.toggle_flag()


def evaluate_flags(coords):
    flags = 0
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx == dy == 0:
                continue
            x = coords[0] + dx
            y = coords[1] + dy
            if x < 0 or y < 0 or x >= width or y >= height:
                continue
            if grid[x][y].is_flagged:
                flags += 1
    return flags


def open_cell(coords=None, visited_cells=None):
    global grid
    do_flagging = False
    if coords is None:  # values for first level of recursion
        coords = current_coords
        visited_cells = [coords]
        cell = grid[coords[0]][coords[1]]
        if cell.is_flagged:
            return
        if cell.is_mine:
            return -1

        flags = evaluate_flags(coords)
        do_flagging = (
            cell.adjacent == flags
            and cell.is_opened
        )

    # avoid border
    x, y = coords
    if x < 0 or y < 0 or x >= width or y >= height:
        return visited_cells
    else:
        cell = grid[coords[0]][coords[1]]

    if do_flagging:
        if cell.is_flagged:
            return visited_cells
        elif cell.is_mine and not cell.is_flagged:
            return -1
    else:
        if cell.is_opened or cell.is_flagged:
            return visited_cells
        else:
            if cell.is_mine:
                return -1
            else:
                cell.is_opened = True
                cell.is_flagged = False

    if cell.adjacent != 0 and not do_flagging:
        return visited_cells

    visited_cells.append(coords)

    # check all neighbouring cells which have not yet been visited
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx == dy == 0:  # avoid current cell
                continue
            x = coords[0] + dx
            y = coords[1] + dy
            if [x, y] not in visited_cells:
                result = open_cell([x, y], visited_cells)
                if result == -1:  # found mine
                    return -1
                visited_cells = result
    return visited_cells


def step(next_move):
    global current_coords, first_move, game_ended
    open_cell_val = None
    message = ''
    if re.match('^[A-Za-z]{1}[0-9]{1,2}$', next_move):
        current_coords[1] = ROWS.find(next_move[0].lower())
        current_coords[0] = int(next_move[1:])-1
        open_cell_val = open_cell()
    elif re.match('^[Ff]{1}[A-Za-z]{1}[0-9]{1,2}$', next_move):
        current_coords[1] = ROWS.find(next_move[1].lower())
        current_coords[0] = int(next_move[2:])-1
        flag()

    if not first_move:
        clear_screen()
    message = print_grid()
    print('Remaining:',
          mines - evaluate_cell_attribute('is_flagged'),
          ' ' * 10)
    if open_cell_val is not None:
        if open_cell_val == -1:
            game_ended = "lose"
        if evaluate_cell_attribute('is_opened') == width * height - mines:
            game_ended = 'win'
    first_move = False

    if game_ended:
        message = end()
        message += '\n'
        message += print_grid()

    return message


def evaluate_cell_attribute(attr):
    attr_value = 0
    for x in range(width):
        for y in range(height):
            if getattr(grid[x][y], attr):
                attr_value += 1
    return attr_value


def clear_screen():
    sys.stdout.write(u"\u001b[" + str(5 + height*2) + "A")  # Move up
    print(u"\u001b[1000D")


def print_grid():
    grid_msg = ''
    # header
    grid_msg += '\n|_|'
    print('\n   ', end='')
    # draw horizontal coordinates
    for x in range(width):
        grid_msg += '%i|' % (x+1)
        print('% 4i' % (x+1), end='')

    grid_msg += '\n|----' + '|----' * (width-1) +'|----|'
    print('\n    ╔═══' + '╤═══' * (width-1) + '╗')
    for y in range(height):
        if y > 0:
            # grid_msg += '    ╟───' + '┼───' * (width-1) + '╢'
            print('    ╟───' + '┼───' * (width-1) + '╢')
        # draw vertical coordinates
        # grid_msg += '\n ' + ROWS[y] + '  ║'
        grid_msg += '\n|' + ROWS[y] + '|'
        print(' ' + ROWS[y] + '  ║', end='')
        for x in range(width):
            if x:
                # grid_msg += '│'
                print('│', end='')
            output = grid[x][y].get_output()
            output = ' %s ' % output
            if current_coords[0] == x and current_coords[1] == y:
                output = output
            # is_mine = 'X' if grid[x][y].is_mine else ' '
            grid_msg += ' ' + output + ' |'
            print(output, end='')
        # grid_msg += '\n'
        print('║')
    print('    ╚═══' + '╧═══' * (width-1) + '╝')
    return grid_msg

def end_game():
    for x in range(width):
        for y in range(height):
            cell = grid[x][y]
            if cell.is_mine:
                cell.is_opened = True


def save_highscores(date, game_time, size, mines):
    home = os.environ['HOME']
    if '.termine' not in os.listdir(home):
        os.makedirs(os.path.join(home, '.termine'))
    filepath = os.path.join(home, '.termine', 'highscores')
    with open(filepath, 'a') as f:
        f.write("{} {} {} {}\n".format(date, game_time, size, mines))


def print_highscores():
    home = os.environ['HOME']
    if (
            '.termine' not in os.listdir(home)
            and 'highscores' not in os.path.join(home, '.termine')
    ):
        print('No highscores yet.')
    else:
        filepath = os.path.join(home, '.termine', 'highscores')
        with open(filepath, 'r') as f:
            highs = list(f)  #.readlines()
        # header
        print("\n{:<26} {:<8} {:<8} {:<8}\n".format("Date",
                                                 "Score",
                                                 "Size",
                                                 "Mines"))
        # scores
        highs = [line.split(' ') for line in highs]
        for line in sorted(highs, key=lambda l: (l[2], l[3], l[1])):
            # print(line)
            date, game_time, size, mines = line
            date = time.strftime("%a %x %X", time.localtime(float(date)))
            print("{:<26} {:<8.2f} {:<8} {}".format(date, float(game_time), size, mines), end='')
        sys.exit()

def init():
    global grid, current_coords, start_time, game_ended, first_move
    message = ''
    grid = generate_grid(width, height, mines)
    message = print_grid()
    compute_grid()
    current_coords = [0, 0]

    start_time = time.time()
    game_ended = False
    first_move = True
    return message

def end():
    message = ''
    end_game()
    # print_grid()
    game_time = time.time() - start_time
    if game_ended == "lose":
        message = "Game over. Time: {:.2f}".format(game_time)
        print(message)
    if game_ended == "win":
        message = "You win! Time: {:.2f}".format(game_time)
        print(message)
        # save_highscores(start_time, game_time, args.gridsize, mines)
    return message

def menu():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='A terminal minesweeper clone.\n'
        '  Controls:\n'
        '    Spacebar: open a cell\n'
        '    F:        flag\n'
        '    Q or ^C:  quit'
        )
    parser.add_argument('-hs', '--highscores', action='store_true',
                        help='Print highscores')
    parser.add_argument('-gs', '--gridsize', metavar='WxH',
                        type=str, default='8x8',
                        help='Size of the grid')
    parser.add_argument('-m', '--mines', metavar='N',
                        type=int, default=10,
                        help='Number of mines')
    args = parser.parse_args()

    if args.highscores:
        print_highscores()
    mines = args.mines
    match = re.match('([0-9]+)x([0-9]+)', args.gridsize)
    try:
        width, height = (int(g) for g in match.groups())
    except:
        print('    Please specify a grid size of form WidthxHeight')
        sys.exit(1)

    if mines > width * height:
        print('    Error: Number of mines too high')
        sys.exit(1)
    if mines < 1:
        print('    Error: Number of mines too low')
        sys.exit(1)
