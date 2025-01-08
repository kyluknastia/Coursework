#include <iostream>
#include <vector>
#include <string>
#include <cstdlib>
#include <limits>
using namespace std;

class Game {
private:
    vector<vector<int>> board; // ���������� ������ (0 - ������� ������, 1 - �����, 2 - ���)
    int currentPlayer; // ��� ����� ���(1 - ����, 2 - ���)
    int geeseCount; // ������ ����� ����������
    bool gameOver; // �� ���������� ���

public:
    Game() : board(8, vector<int>(8, 0)), currentPlayer(1), geeseCount(12), gameOver(false) {
        setupBoard(); // ��������� ����� �� �����
    }

    void setupBoard() {
        // ���������� ��� ����� ������
        for (int row = 0; row < 8; row++) {
            for (int col = 0; col < 8; col++) {
                board[row][col] = 0;
            }
        }

        // ����������� �����
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 8; col++) {
                if ((row + col) % 2 == 0) {
                    board[row][col] = 1;  // ����
                }
            }
        }
        // ������ ����
        board[7][1] = 2;  // ���
    }

    bool isValidPosition(int row, int col) {
        return row >= 0 && row < 8 && col >= 0 && col < 8 && (row + col) % 2 == 0;
    }

    void displayBoard() {
#ifdef _WIN32
        system("cls");
#else
        system("clear");
#endif

        cout << "\n  Fox and Geese\n\n";
        cout << "    0 1 2 3 4 5 6 7  \n";
        cout << "  -------------------\n";

        for (int row = 0; row < 8; row++) {
            cout << row << " | ";
            for (int col = 0; col < 8; col++) {
                if ((row + col) % 2 == 1) {
                    cout << "  ";  // ��� �������
                }
                else {
                    char symbol = '.';
                    if (board[row][col] == 1) symbol = 'G';
                    if (board[row][col] == 2) symbol = 'F';
                    cout << symbol << " ";
                }
            }
            cout << "|\n";
        }
        cout << "  -------------------\n\n";
        cout << "Geese remaining: " << geeseCount << "\n";
        cout << "Current turn: " << (currentPlayer == 1 ? "Geese" : "Fox") << "\n";
        cout << "Enter move (fromRow fromCol toRow toCol) or q to quit\n";
        cout << "Example: 6 2 5 3\n\n";
    }

    bool isValidMove(int fromRow, int fromCol, int toRow, int toCol, bool& isCapture) {
        isCapture = false; //  ������ �������� ����

        // ����� �������
        if (!isValidPosition(fromRow, fromCol) || !isValidPosition(toRow, toCol))
            return false;

        // ��������, �� ��������� ������� ������ ������� ������
        if (board[fromRow][fromCol] != currentPlayer)
            return false;

        // ��������, �� ������� ������� �����
        if (board[toRow][toCol] != 0)
            return false;

        int rowDiff = abs(toRow - fromRow);
        int colDiff = abs(toCol - fromCol);

        // ��� �����
        if (currentPlayer == 1) {
            // ���� ������ ������ ����� ������ �� �������
            return (toRow == fromRow + 1 && colDiff == 1);
        }
        // ��� ������
        else {
            // ճ� �� �������
            if (rowDiff == 1 && colDiff == 1)// �������� �� ���� ����� � ���� �������� �� �������
                return true;

            // ������� ������ ����� ����
            if (rowDiff == 2 && colDiff == 2) {
                int midRow = (fromRow + toRow) / 2;
                int midCol = (fromCol + toCol) / 2;
                if (board[midRow][midCol] == 1) {
                    isCapture = true;
                    return true;
                }
            }
        }
        return false;
    }

    bool makeMove(int fromRow, int fromCol, int toRow, int toCol) {
        bool isCapture;
        if (!isValidMove(fromRow, fromCol, toRow, toCol, isCapture)) {
            cout << "Invalid move! Press Enter to continue...";
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cin.get();
            return false;
        }

        // ������ ���
        board[toRow][toCol] = board[fromRow][fromCol];
        board[fromRow][fromCol] = 0;

        // ���� ���� �'��� ����
        if (isCapture) {
            int midRow = (fromRow + toRow) / 2;
            int midCol = (fromCol + toCol) / 2;
            board[midRow][midCol] = 0;
            geeseCount--;
        }

        return true;
    }

    bool checkWinCondition() {
        // �������� ������� ����
        if (geeseCount <= 5) {
            cout << "\nFox wins! Too many geese have been captured!\n";
            return true;
        }

        // �������� ��������� ���� ������
        bool foxCanMove = false;
        int foxRow = -1, foxCol = -1; // ���� �� ��

        // ��������� ������� ����
        for (int row = 0; row < 8 && foxRow == -1; row++) {
            for (int col = 0; col < 8; col++) {
                if (board[row][col] == 2) {
                    foxRow = row;
                    foxCol = col;
                    break;
                }
            }
        }

        if (foxRow != -1) {
            // ��������� �� ������ ���� ����
            int tempPlayer = currentPlayer;
            currentPlayer = 2;

            // ��������� ����� ����
            for (int dr : {-1, 1}) {
                for (int dc : {-1, 1}) {
                    bool isCapture;
                    if (isValidMove(foxRow, foxCol, foxRow + dr, foxCol + dc, isCapture)) {
                        foxCanMove = true;
                        break;
                    }
                }
                if (foxCanMove) break;
            }

            // ��������� ������
            if (!foxCanMove) {
                for (int dr : {-2, 2}) {
                    for (int dc : {-2, 2}) {
                        bool isCapture;
                        if (isValidMove(foxRow, foxCol, foxRow + dr, foxCol + dc, isCapture)) {
                            foxCanMove = true;
                            break;
                        }
                    }
                    if (foxCanMove) break;
                }
            }

            currentPlayer = tempPlayer;
        }

        // ��� ������,���� �� ���� ������ � ���� ����� ���
        if (!foxCanMove && currentPlayer == 2) {
            cout << "\nGeese win! Fox is trapped!\n";
            return true;
        }

        return false; // ���� �� ���������� ����� ������� 
    }

    void play() {
        string input;
        int fromRow, fromCol, toRow, toCol;

        while (!gameOver) {
            displayBoard();

            cout << "Your move: ";

            // �������� �� ����� � ���
            if (!(cin >> fromRow)) {
                cin.clear();
                cin.ignore(numeric_limits<streamsize>::max(), '\n');
                getline(cin, input);
                if (input == "q" || input == "Q") {
                    cout << "Game ended by player\n";
                    break;
                }
                continue;
            }

            // ������ ���� ����������
            if (!(cin >> fromCol >> toRow >> toCol)) {
                cin.clear();
                cin.ignore(numeric_limits<streamsize>::max(), '\n');
                cout << "Invalid input! Press Enter to continue...";
                cin.get();
                continue;
            }

            //������ ���
            if (makeMove(fromRow, fromCol, toRow, toCol)) {
                gameOver = checkWinCondition();
                if (!gameOver) {
                    currentPlayer = (currentPlayer == 1) ? 2 : 1;
                }
            }
        }

        if (gameOver) {
            displayBoard();
            cout << "\nGame Over! Press Enter to exit...";
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cin.get();
        }
    }
};

int main() {
    Game game;
    game.play();
    return 0;
}