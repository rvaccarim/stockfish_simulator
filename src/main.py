import logging
import os
import copy
import time
import shutil
import chess.engine
import chess.polyglot
import chess.svg

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

output_root = "../output"


def save_match(filename, board, moves):
    with open(f"{filename}.log", "w") as game_file:

        if board.is_checkmate():
            if board.turn == chess.WHITE:
                game_file.write("Black checkmate\n")
            else:
                game_file.write("White checkmate\n")
        else:
            if board.is_stalemate():
                game_file.write("Draw - Stalemate\n")
            else:
                if board.is_insufficient_material():
                    game_file.write("Draw - Insufficient material\n")
                else:
                    if board.is_fivefold_repetition():
                        game_file.write("Draw - Fivefold repetition\n")
                    else:
                        if board.is_seventyfive_moves():
                            game_file.write("Draw - Seventyfive Moves\n")
                        else:
                            game_file.write("Draw - Other\n")

        game_file.write(f"\n{str(board)}\n\n")

        for i, move in enumerate(moves):
            if i % 2 == 0:
                game_file.write(f"White: {str(move)}\n")
            else:
                game_file.write(f"Black: {str(move)}\n")

    boardsvg = chess.svg.board(board=board)
    with open(f"{filename}.svg", "w") as image_file:
        image_file.write(boardsvg)

    svg_image = svg2rlg(f"{filename}.svg")
    renderPM.drawToFile(svg_image, f"{filename}.png", fmt="PNG")
    os.remove(f"{filename}.svg")


def setup_board(starting_moves, use_opening_book):
    board = chess.Board()
    opening_moves = []

    for fm in starting_moves:
        m = chess.Move.from_uci(fm)
        board.push(m)
        opening_moves.append(m)

    book_depth = 22

    if use_opening_book:
        with chess.polyglot.open_reader("D:/Users/frozen/Documents/03_programming/online/stockfish/books/elo-2700.bin") as reader:
            while True:
                found = False

                # uses the first play from the recommended plays according to the opening book
                for entry in reader.find_all(board):
                    board.push(entry.move)
                    opening_moves.append(entry.move)
                    found = True
                    break

                if not found or len(opening_moves) >= book_depth:
                    break

    return board, opening_moves


def play(engine, starting_moves, use_opening_book, matches, depth, log_file, summary_file):
    results = {"1-0": 0,
               "0-1": 0,
               "1/2-1/2": 0,
               "*": 0
               }

    initial_board, initial_moves = setup_board(starting_moves, use_opening_book)

    starting_str = '_'.join(starting_moves)
    output_dir = f"{output_root}/{depth}/{starting_str}"

    for match in range(0, matches):
        tic = time.perf_counter()
        board = copy.deepcopy(initial_board)
        moves = copy.deepcopy(initial_moves)

        while not board.is_game_over():
            result = engine.play(board, chess.engine.Limit(depth=depth), ponder=False)
            board.push(result.move)
            moves.append(result.move)

        results[board.result()] += 1

        # record match, saves log and a png image of the board's final state
        if use_opening_book:
            filename = f"{output_dir}/book_game_{match + 1}"
        else:
            filename = f"{output_dir}/game_{match + 1}"

        save_match(filename, board, moves)
        toc = time.perf_counter()

        log_str = f'Book: {str(use_opening_book):5s} Depth: {depth} {starting_str}  Match: {str(match + 1):>3s}    W:{str(results["1-0"]):>3s}  D:{str(results["1/2-1/2"]):>3s}  B:{str(results["0-1"]):>3s}  {str(len(moves)):>3s} moves {toc - tic:0.4f} seconds '
        print(log_str)
        log_file.write(log_str + "\n")
        log_file.flush()

    summary_file.write(
        f'Book: {str(use_opening_book):5s} Depth: {depth} {starting_str}  W:{str(results["1-0"]):>3s}  D:{str(results["1/2-1/2"]):>3s}  B:{str(results["0-1"]):>3s}\n')
    summary_file.flush()


def setup_output(output_dir, depths, moves_list):
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)

    for d in depths:
        for moves in moves_list:
            moves_str = "_".join(moves)
            os.makedirs(f"{output_dir}/{d}/{moves_str}")


def simulate():
    starting_moves = [["e2e4", "e7e5"],
                      ["e2e4", "c7c5"],
                      ["d2d4", "g8f6"],
                      ["d2d4", "d7d5"],
                      ["g1f3"],
                      ["c2c4"],
                      ["f2f3"]]

    depths = [20]
    setup_output(output_root, depths, starting_moves)

    # logging.basicConfig(level=logging.DEBUG)
    engine = chess.engine.SimpleEngine.popen_uci("D:/Users/frozen/Documents/99_temp/stockfish_12/stockfish.exe")
    engine.configure({"Threads": 6})
    engine.configure({"Hash": 4096})
    engine.configure({"SyzygyPath": "D:/Users/frozen/Documents/03_programming/online/stockfish/syzygy"})

    with open(f"{output_root}/log.txt", "w") as log:
        with open(f"{output_root}/summary.txt", "w") as summary:
            for d in depths:
                for s_moves in starting_moves:
                    play(engine, s_moves, use_opening_book=True, matches=2, depth=d, log_file=log,
                         summary_file=summary)
                    play(engine, s_moves, use_opening_book=False, matches=2, depth=d, log_file=log,
                         summary_file=summary)

                    print("")
                    log.write("\n")
                    summary.write("\n")

    engine.quit()


if __name__ == "__main__":
    simulate()

