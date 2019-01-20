# A sudoku solver for arbitrarily-sized boards. This program uses Donald Knuth's "Algorithm X" to efficiently
# find the most-constrained moves for a given board; that is, it finds empty cells with the fewest candidate
# values and attempts one, then updates all other constraints related to that row, column, and block to
# account for the new value. This is done recursively until no candidates exist in an empty cell, at which
# point it steps back and attempts other values. If the board is filled, a solution is generated, then the
# program steps back to find more solutions.

def main():
    import argparse

    parser = argparse.ArgumentParser(description = 'Solve a Sudoku board.')
    parser.add_argument('input', help = 'file containing non-negative integers separated by commas and newlines', nargs = '?', default = None)
    parser.add_argument('output', help = 'destination file for solutions (default: "solutions.txt")', nargs = '?', default = 'solutions.txt')
    parser.add_argument('-n', help = 'number of solutions to calculate (default: 1)', type = int, nargs = '?', default = 1)
    parser.add_argument('--example', help = 'create a formatted input file "exampleboard.txt"', action = 'store_true')
    args = parser.parse_args()
    if args.example:
        make_example()
        return
    if not args.input:
        parser.print_help()
        return
    board = make_board(args.input)
    check_board(board)
    write_solutions(args.output, board, args.n)

def make_example():
    import os

    f = open('exampleboard.txt', 'w')
    f.write('''# Integers must be non-negative and separated by commas. Whitespace characters are ignored.
0,0,0,7,9,0,0,5,0
3,5,2,0,0,8,0,4,0
0,0,0,0,0,0,0,8,0
0,1,0,0,7,0,0,0,4
6,0,0,3,0,1,0,0,8
9,0,0,0,8,0,0,1,0
0,2,0,0,0,0,0,0,0
0,4,0,5,0,0,8,9,1
0,8,0,0,3,7,0,0,0''')
    print('Example file created: ' + os.path.realpath(f.name))
    f.close()

def make_board(filename):
    import re

    f = open(filename, 'r')
    board = []
    s = f.readlines()
    for row in s:
        if row[0] == '#': continue
        board.append([])
        while '  ' in row: row = row.replace('  ', ' ')
        row = re.split(', |,| ', row)
        for x in row:
            try:
                board[-1].append(int(x))
            except ValueError:
                raise Exception('Non-integer found in input file: \'{}\''.format(x))
    return board

def check_board(board):
    board_size_message = 'Board length must be a square (i.e. 1x1, 4x4, 9x9...).'
    row_size_message = 'Row {} (1-indexed) contains {} elements: should contain {}.'
    element_message = '{0}x{0} board may only contain integers 0-{0}: {1} found at ({2},{3}) (1-indexed).'
    N = len(board)
    if (N ** 0.5) % 1 != 0: raise Exception(board_size_message)
    for i in range(N):
        if len(board[i]) != N: raise Exception(row_size_message.format(i + 1, len(board[i]), N))
        for j in range(len(board[i])):
            if not 0 <= board[i][j] <= N:
                raise Exception(element_message.format(N, board[i][j], i + 1, j + 1))

def write_solutions(filename, board, display):
    import os
    
    f = open(filename, 'w')
    print("Printing solutions to file: " + os.path.realpath(f.name))
    f.write("Initial board:")
    for row in board:
        f.write('\n' + ','.join(str(x) for x in row))

    dashes = '\n' + '-' * len(','.join(str(x) for x in range(1, len(board) + 1)))
    display = -1 if display == 0 else display
    i = None
    for i, b in enumerate(solve(board), 1):
        if i == display + 1:
            i -= 1
            display = -2
            break
        f.write(dashes)
        f.write('\nSolution {}:'.format(i))
        for row in b:
            f.write('\n' + ','.join(str(x) for x in row))
    
    if not i:
        f.write(dashes + '\nNo solutions found.')
        f.close()
        raise Exception('Invalid board.')
    elif display == -2:
        print('Done! Printed first {} solutions.'.format(i) if i > 1 else 'Done! Printed first solution.')
        print('To see more solutions, use "-n [int]" argument (0 for all solutions).')
    else:
        print('Done! {} solution{} found.'.format(i, 's' if i > 1 else ''))
    f.write('\n\n{} solution{} found.'.format(i, 's' if i > 1 else ''))
    f.close()



def solve(board):    
    from copy import deepcopy

    N = len(board)
    B = int(N ** 0.5)
    
    X = dict()
    for i in range(N):
        for j in range(N):
            X[('rowcol', i, j)] = set()          # Constraint 1: One value per row-col intersection (indices 0-8, 0-8)
            X[('rownum', i, j+1)] = set()        # Constraint 2: One number per row (index 0-8, number 1-9)
            X[('colnum', i, j+1)] = set()        # Constraint 3: One number per column (index 0-8, number 1-9)
            X[('blcnum', i, j+1)] = set()        # Constraint 4: One number per block (index 0-8, number 1-9)
            
    Y = dict()
    for row in range(N):                         # Populate Y with constraints per cell value
        for col in range(N):
            blc = B * (row // B) + col // B
            for num in range(1, N + 1):
                Y[(row, col, num)] = [
                    ('rowcol', row, col),
                    ('rownum', row, num),
                    ('colnum', col, num),
                    ('blcnum', blc, num)]
                    
    for item, row in Y.items():                  # Populate X with possible cell values per constraint
        for i in row:
            X[i].add(item)
            
    try:
        for row in range(N):                     # Select board clues, do not save temporary results
            for col in range(N):
                num = board[row][col]
                if num:
                    select(X, Y, (row, col, num))
    except KeyError:                             # Catches KeyError exception from select() call
        raise Exception('Invalid board.')
        
    for solution in attempt(X, Y, []):           # Generate solutions
        b = deepcopy(board)
        for (r, c, n) in solution:
            b[r][c] = n
        yield b

def attempt(X, Y, solution):
    if not X:                                    # If no possible cell values left to test, return all attempted values
        yield solution
    else:
        L = 10
        for a in X:                              # Quickly find smallest list of "rows" (possible cell values) in X
            if len(X[a]) < L:
                i = a
                L = len(X[a])
            if L == 1: break
        for row in list(X[i]):
            solution.append(row)
            cols = select(X, Y, row)             # Remove constraints and candidates from X
            for s in attempt(X, Y, solution):
                yield s                          # Create generator of all attempted values from here down
            deselect(X, Y, row, cols)            # If not done, re-add stored constraints and candidates to X
            solution.pop()

def select(X, Y, row):                           # Raises KeyError exception if constraint not in X, indicating invalid board
    cols = []
    for i in Y[row]:                             # For each "column" or constraint in Y from selected cell value ("row")...
        for j in X[i]:                           # ...and each cell value satisfying constraints...
            for k in Y[j]:                       # ...and each constraint from satisficing cell values...
                if k != i:              
                    X[k].remove(j)               # ...remove from X all cell values in those constraints
        cols.append(X.pop(i))                    # Also, remove from X that "column"/constraint and all cell values, store in temp array
    return cols

def deselect(X, Y, row, cols):
    for i in Y[row][::-1]:                       # For each "column" or constraint in Y from selected cell value ("row")...
        X[i] = cols.pop()                        # ...insert stored "column"/constraint and all cell values
        for j in X[i]:                           # Also, for each stored cell value...
            for k in Y[j]:                       # ...and each relevant constraint...
                if k != i:
                    X[k].add(j)                  # ...re-add to X all cell values in those constraints

if __name__ == "__main__":
    main()
