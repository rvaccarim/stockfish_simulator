import chess.polyglot

first_moves = ["c2c4"]

board = chess.Board()
moves = []

for fm in first_moves:
    moves.append(fm)
    m = chess.Move.from_uci(fm)
    board.push(m)

book_depth = 22

with chess.polyglot.open_reader("D:/Users/frozen/Documents/03_programming/online/stockfish/books/elo-2700.bin") as reader:
    while True:
        found = False
        for entry in reader.find_all(board):
            found = True
            board.push(entry.move)
            moves.append(str(entry.move)) 
            break
    
        if not found or len(moves) >= book_depth:
            break

line = " ".join(moves)
print(line)
