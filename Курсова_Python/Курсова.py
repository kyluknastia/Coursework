import pygame
import sys
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Ініціалізація Pygame
pygame.init()

# Константи
WINDOW_WIDTH = 1200  # Ширина вікна
WINDOW_HEIGHT = 800  # Висота вікна
BOARD_SIZE = 800  # Розмір дошки
CELL_SIZE = BOARD_SIZE // 8  # Розмір клітинки
PIECE_RADIUS = CELL_SIZE // 3  # Радіус фігури
SIDEBAR_WIDTH = WINDOW_WIDTH - BOARD_SIZE  # Ширина бічної панелі
ANIMATION_SPEED = 0.05  # Швидкість анімації

# Кольори
BLACK = (0, 0, 0)  # Чорний
WHITE = (255, 255, 255)  # Білий
BOARD_LIGHT = (222, 184, 135)  # Світло-коричневий
BOARD_DARK = (139, 69, 19)  # Темно-коричневий
PIECE_BLACK = (64, 64, 64)  # Колір гусей (темно-сірий)
PIECE_RED = (178, 34, 34)  # Колір лиса (темно-червоний)
PIECE_CENTER = (192, 192, 192)  # Світло-сірий центр фігур
HIGHLIGHT = (255, 215, 0)  # Жовте підсвічування
SIDEBAR_GREEN = (144, 238, 144)  # Світло-зелений
DARK_GREEN = (34, 139, 34)  # Темно-зелений для рамок


class GameState(Enum): #перелічуваний тип
    """Стани гри"""
    PLAYING = 1  # Гра триває
    FOX_WIN = 2  # Переміг лис
    GEESE_WIN = 3  # Перемогли гуси


class GameMode(Enum): #перелічуваний тип
    """Режими гри"""
    PVP = "Гравець проти гравця"
    PVE_GEESE = "Гравець за гусей"
    PVE_FOX = "Гравець за лиса"


@dataclass
class Move:
    """Клас для представлення ходу"""
    start: Tuple[int, int]  # Початкова позиція (рядок, стовпець)
    end: Tuple[int, int]  # Кінцева позиція (рядок, стовпець)
    capture: bool = False  # Чи є хід захопленням
    captured_position: Optional[Tuple[int, int]] = None  # Позиція захопленої фігури


class AnimationEffect:
    """Клас для анімаційних ефектів"""

    def __init__(self, position: Tuple[int, int], effect_type: str):
        self.position = position
        self.effect_type = effect_type
        self.lifetime = 30  # Тривалість анімації
        self.alpha = 255  # Прозорість

    def update(self) -> bool:
        """Оновлення стану анімації"""
        self.lifetime -= 1 # Зменшується тривалість життя ефекту
        self.alpha = int((self.lifetime / 30) * 255)
        return self.lifetime <= 0 # Повертається True, якщо ефект завершився


class AI:
    """Клас для штучного інтелекту"""

    def __init__(self, game, player_id):
        self.game = game # посилання на об'єкт гри
        self.player_id = player_id # ідентифікатор гравця
        self.max_depth = 3  # Глибина пошуку

    def evaluate_position(self) -> float:
        """Оцінка поточної позиції"""
        if self.player_id == 2:  # Для лиса
            # Знаходимо позицію лиса
            fox_pos = None
            for row in range(8):
                for col in range(8):
                    if self.game.board[row][col] == 2: #знаходимо лиса на дошці
                        fox_pos = (row, col)
                        break
                if fox_pos:
                    break

            if not fox_pos:
                return float('-inf') #програш

            score = 0  #підрахунку вигідності поточної позиції лиса
            row, col = fox_pos

            # Бали за з'їджених гусей
            score += (12 - self.game.geese_count) * 100 #отримує 100 балів за кожного з'їдженого гусака

            # Перевіряємо можливості захоплення
            capture_moves = [move for move in self.get_all_moves() if move.capture] #перевіряє, чи є поточний хід захопленням фігури супротивника
            #отримує 50 балів за кожну можливість захоплення гусака
            score += len(capture_moves) * 50 # кількість ходів, що є захопленнями

            # Оцінка позиції на дошці
            center_dist = abs(3.5 - row) + abs(3.5 - col)
            score -= center_dist * 5 #кожен крок від центру віднімає 5 балів від оцінки

            return score

        else:  # Для гусей
            score = self.game.geese_count * 100 #кожен залишений гусак дає 100 балів
            return score

    def get_all_moves(self) -> List[Move]:
        """Отримати всі можливі ходи"""
        moves = [] # порожній список
        # Пошук всіх можливих ходів для поточного гравця
        for row in range(8):
            for col in range(8):
                if self.game.board[row][col] == self.player_id: # чи є фігура поточного гравця на клітинці (row, col)
                    moves.extend(self.game.get_valid_moves(row, col))
        return moves

    def get_best_move(self) -> Optional[Move]: #повертає об'єкт типу Move
        """Отримати найкращий хід"""
        moves = self.get_all_moves()
        if not moves:
            return None

        # Для лиса спочатку перевіряємо ходи з захопленням
        if self.player_id == 2:
            capture_moves = [move for move in moves if move.capture] #поточний хід є захопленням фігури супротивника
            if capture_moves:
                return capture_moves[0] #повертає перший такий хід

        # Якщо немає ходів з захопленням, вибираємо випадковий
        return random.choice(moves)


class Game:
    def __init__(self):
        # Ініціалізація вікна та шрифтів
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Лис та гуси")
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.game_mode = None #поточного режиму гри
        self.show_menu = True
        self.buttons = self._create_menu_buttons()
        self.reset_game() #скидає стан гри до початкового

    def reset_game(self):
        """Скидання гри до початкового стану"""
        self.board = [[0 for _ in range(8)] for _ in range(8)] #2D список (дошка гри) розміру 8x8
        self.selected_piece = None  # ще немає вибраної фігури
        self.current_player = 1  # 1 - гуси, 2 - лис
        self.game_state = GameState.PLAYING
        self.geese_count = 12  # Початкова кількість гусей
        self.last_move = None
        self.possible_moves = []
        self.visual_effects = []
        self.animation = None
        self.pending_move = None #немає очікуваного ходу для виконання
        self.fox_score = 0
        self.geese_score = 0
        self.ai = None
        self.setup_board() #ініціалізації початкового стану на дошці

    def setup_board(self):
        """Розстановка фігур на початку гри"""
        # Розставляємо гусей на чорних клітинках
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 0:
                    self.board[row][col] = 1

        # Ставимо лиса
        self.board[7][7] = 2

    def is_valid_position(self, row: int, col: int) -> bool:
        """Перевірка чи є позиція допустимою"""
        return 0 <= row < 8 and 0 <= col < 8 and (row + col) % 2 == 0

    def get_valid_moves(self, row: int, col: int) -> List[Move]:
        """Отримання всіх можливих ходів для фігури"""
        moves = [] #список, в який будуть додаватися всі допустимі ходи для фігури
        piece = self.board[row][col]  # фігура

        if piece == 1:  # Гуси
            # Гуси ходять тільки вперед по діагоналі
            for dc in [-1, 1]:
                new_row, new_col = row + 1, col + dc
                if self.is_valid_position(new_row, new_col) and self.board[new_row][new_col] == 0:
                    moves.append(Move((row, col), (new_row, new_col)))

        elif piece == 2:  # Лис
            # Лис ходить в будь-якому напрямку по діагоналі
            for dr in [-1, 1]:
                for dc in [-1, 1]:
                    # Звичайний хід
                    new_row, new_col = row + dr, col + dc
                    if self.is_valid_position(new_row, new_col):
                        if self.board[new_row][new_col] == 0:
                            moves.append(Move((row, col), (new_row, new_col)))
                        # Перевірка можливості захоплення
                        elif (self.board[new_row][new_col] == 1 and
                              self.is_valid_position(new_row + dr, new_col + dc) and
                              self.board[new_row + dr][new_col + dc] == 0):
                              moves.append(Move((row, col),(new_row + dr, new_col + dc),
                              capture=True,
                              captured_position=(new_row, new_col)
                            ))

        return moves

    def make_move(self, move: Move, skip_animation: bool = False):
        """Виконання ходу"""
        if skip_animation:
            self.complete_move(move) # завершує хід
        else:
            if self.animation:
                return

            self.animation = AnimationEffect(move.start, "move")
            self.last_move = move
            self.pending_move = move #чекає на виконання після завершення анімації

    def complete_move(self, move: Move):
        """Завершення ходу"""
        if not move: #хід не переданий
            return

        start_row, start_col = move.start
        end_row, end_col = move.end

        # Виконуємо хід
        piece = self.board[start_row][start_col]
        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = 0

        # Обробляємо захоплення
        if move.capture and piece == 2:  # Тільки лис може захоплювати
            captured_row, captured_col = move.captured_position
            if self.board[captured_row][captured_col] == 1:  # Перевіряємо що захоплюється гуска
                self.board[captured_row][captured_col] = 0
                self.geese_count -= 1
                self.fox_score += 1
                self.visual_effects.append(
                    AnimationEffect(move.captured_position, "capture")
                )

        # Перевіряємо умови перемоги
        self._check_win_condition()

        # Змінюємо гравця
        self.current_player = 3 - self.current_player

    def _check_win_condition(self):
        """Перевірка умов перемоги"""
        # Перемога лиса, якщо з'їв 7 і більше гусей
        if self.geese_count <= 5:
            self.game_state = GameState.FOX_WIN
            return

        # Перевірка чи може лис ходити (оточення)
        fox_pos = None
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == 2:
                    fox_pos = (row, col)
                    break
            if fox_pos:
                break

        if fox_pos:
            can_fox_move = bool(self.get_valid_moves(*fox_pos)) #усі можливі ходи для фігури   self.get_valid_moves(fox_pos[0], fox_pos[1])
            if not can_fox_move:
                self.game_state = GameState.GEESE_WIN
                return

        # Перевірка чи можуть ходити гуси
        if self.current_player == 1:
            can_geese_move = False
            for row in range(8):
                for col in range(8):
                    if self.board[row][col] == 1:
                        if self.get_valid_moves(row, col):
                            can_geese_move = True
                            break
                if can_geese_move:
                    break

            if not can_geese_move and self.geese_count >= 7:
                self.game_state = GameState.GEESE_WIN

    def update(self):
        """Оновлення стану гри"""
        # Оновлення анімації
        if self.animation:
            if self.animation.update(): # якщо анімація завершена
                self.complete_move(self.pending_move) # скидаємо до початкового стану
                self.animation = None
                self.pending_move = None
                return  # Виходимо після завершення анімації

        # Оновлення візуальних ефектів
        self.visual_effects = [effect for effect in self.visual_effects if not effect.update()] #список усіх активних візуальних ефектів
        # список візуальних ефектів, в якому залишаються лише ті ефекти, що ще активні

        # Хід ШІ
        if (not self.animation and  #жоден рух не відображається
                not self.pending_move and #жоден хід не очікується для завершення
                self.game_state == GameState.PLAYING): #гра активна, і хтось має зробити хід

            # Перевіряємо чи має ходити ШІ
            ai_should_move = (
                    (self.game_mode == GameMode.PVE_GEESE and self.current_player == 2) or # режим гри встановлений як PVE_GEESE
                    (self.game_mode == GameMode.PVE_FOX and self.current_player == 1)
            )

            if ai_should_move and self.ai:
                move = self.ai.get_best_move()
                if move:
                    self.make_move(move)

    def handle_click(self, pos: Tuple[int, int]):
        """Обробка кліку мишею"""
        if self.animation or pos[0] >= BOARD_SIZE:
            return

        col = pos[0] // CELL_SIZE   # ділимо координату миші на розмір клітинки і отримуємо номер клітинки в цілому числі
        row = pos[1] // CELL_SIZE

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        # Перевіряємо чи це правильний гравець
        current_piece = self.board[row][col]  # присвоюється значення фігури на клітинці, на яку було клацнуто мишею

        if self.selected_piece is None: # чи немає вже вибраної фігури
            if current_piece == self.current_player: # фігура на натиснутій клітинці повинна відповідати фігурі поточного гравця
                if ((self.game_mode == GameMode.PVE_GEESE and self.current_player == 1) or
                        (self.game_mode == GameMode.PVE_FOX and self.current_player == 2) or
                        self.game_mode == GameMode.PVP):
                    self.selected_piece = (row, col)
                    self.possible_moves = self.get_valid_moves(row, col)
        else:
            # Шукаємо хід у можливих ходах
            move = next((move for move in self.possible_moves
                         if move.end == (row, col)), None) # порівнюються координати клітинки з кінцевими координатами кожного можливого ходу
            if move:
                self.make_move(move)

            self.selected_piece = None
            self.possible_moves = []

    def draw_board(self):
        """Малювання дошки"""
        self.screen.fill(WHITE)

        for row in range(8):
            for col in range(8):
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                color = BOARD_LIGHT if (row + col) % 2 == 1 else BOARD_DARK
                pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE, CELL_SIZE))

    def draw_pieces(self):
        """Малювання фігур"""
        for row in range(8):
            for col in range(8):
                if self.board[row][col] != 0:
                    x = col * CELL_SIZE + CELL_SIZE // 2
                    y = row * CELL_SIZE + CELL_SIZE // 2
                    color = PIECE_BLACK if self.board[row][col] == 1 else PIECE_RED

                    # Малюємо фігуру
                    pygame.draw.circle(self.screen, color, (x, y), PIECE_RADIUS)
                    pygame.draw.circle(self.screen, PIECE_CENTER, (x, y), PIECE_RADIUS // 2)

    def draw_highlights(self):
        """Малювання підсвічування"""
        if self.selected_piece:
            row, col = self.selected_piece
            x = col * CELL_SIZE
            y = row * CELL_SIZE

            surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA) #створюється нова поверхня розміром з одну клітинку для прозорого зображення
            pygame.draw.rect(surface, (*HIGHLIGHT, 128),(0, 0, CELL_SIZE, CELL_SIZE)) #малюється прямокутник
            self.screen.blit(surface, (x, y)) #переносимо прозору поверхню на основний екран

            # Підсвічування можливих ходів
            for move in self.possible_moves:
                end_row, end_col = move.end
                x = end_col * CELL_SIZE
                y = end_row * CELL_SIZE

                surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA) #створюється нова поверхня
                color = (*PIECE_RED, 128) if move.capture else (*HIGHLIGHT, 128)
                pygame.draw.rect(surface, color, (0, 0, CELL_SIZE, CELL_SIZE)) #малюється прямокутник
                self.screen.blit(surface, (x, y)) #переносимо прозору поверхню на основний екран

    def draw_sidebar(self):
        """Малювання бічної панелі"""
        # Фон бічної панелі
        sidebar_x = BOARD_SIZE + 10 # починається бічна панель
        sidebar_width = WINDOW_WIDTH - BOARD_SIZE - 20 # ширина бічної панелі
        sidebar_rect = pygame.Rect(BOARD_SIZE, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, SIDEBAR_GREEN, sidebar_rect)
        pygame.draw.line(self.screen, DARK_GREEN, (BOARD_SIZE, 0),
                         (BOARD_SIZE, WINDOW_HEIGHT), 2)

        text_margin = 20 # Відступ тексту від лівого краю бічної панелі
        current_y = 30 # Поточна вертикальна позиція для тексту у бічній панелі
        line_spacing = 35 # Відстань між текстовими рядками

        # Заголовок
        title = self.font.render("Лис та гуси", True, BLACK) #створює графічну поверхню
        title_rect = title.get_rect(left=sidebar_x + text_margin, top=current_y) # горизонтальну позицію заголовка  # вертикальну позицію заголовка
        self.screen.blit(title, title_rect)
        current_y += line_spacing * 1.5 # збільшуємо вертикальну позицію

        # Режим гри
        mode_text = self.game_mode.value if self.game_mode else "Оберіть режим гри"
        mode = self.font.render(mode_text, True, BLACK) #створює графічну поверхню
        mode_rect = mode.get_rect(left=sidebar_x + text_margin, top=current_y)
        self.screen.blit(mode, mode_rect)
        current_y += line_spacing * 1.5

        # Поточний хід
        if self.game_state == GameState.PLAYING:
            current_text = f"Хід: {'Лиса' if self.current_player == 2 else 'Гусей'}"
        else:
            if self.game_state == GameState.FOX_WIN:
                current_text = "Лис переміг!"
            else:
                current_text = "Гуси перемогли!"

            # Додаємо прямокутник для виділення повідомлення про перемогу
            msg_rect = pygame.Rect(sidebar_x, current_y - 5,
                                   sidebar_width - 20, line_spacing + 10)
            pygame.draw.rect(self.screen, BOARD_LIGHT, msg_rect)
            pygame.draw.rect(self.screen, DARK_GREEN, msg_rect, 2)

        text = self.font.render(current_text, True, BLACK) #створює графічну поверхню
        text_rect = text.get_rect(left=sidebar_x + text_margin, top=current_y)
        self.screen.blit(text, text_rect)
        current_y += line_spacing * 1.5

        # Кількість гусей
        geese_text = f"Гусей на полі: {self.geese_count}"
        text = self.font.render(geese_text, True, BLACK) #створює графічну поверхню
        text_rect = text.get_rect(left=sidebar_x + text_margin, top=current_y)
        self.screen.blit(text, text_rect)
        current_y += line_spacing

        # Рахунок
        score_text = "Рахунок:"
        text = self.font.render(score_text, True, BLACK) #створює графічну поверхню
        text_rect = text.get_rect(left=sidebar_x + text_margin, top=current_y) #горизонтальну позиція #вертикальну позиція
        self.screen.blit(text, text_rect)
        current_y += line_spacing

        # Рахунок лиса
        fox_score_text = f"Лис: {self.fox_score}"
        text = self.font.render(fox_score_text, True, PIECE_RED) #створює графічну поверхню
        text_rect = text.get_rect(left=sidebar_x + text_margin * 2, top=current_y) #горизонтальну позиція #вертикальну позиція
        self.screen.blit(text, text_rect)
        current_y += line_spacing

        # Рахунок гусей
        geese_score_text = f"Гуси: {self.geese_score}"
        text = self.font.render(geese_score_text, True, PIECE_BLACK) #створює графічну поверхню
        text_rect = text.get_rect(left=sidebar_x + text_margin * 2, top=current_y) #горизонтальну позиція #вертикальну позиція
        self.screen.blit(text, text_rect)
        current_y += line_spacing * 1.5

        # Правила гри
        rules_text = [
            "Правила гри:",
            "• Гуси ходять по діагоналі вперед",
            "• Лис ходить по діагоналі в будь-який бік",
            "• Лис може перестрибувати через гусей",
            "  та їсти їх",
            "• Гуси перемагають, якщо:",
            "  - оточать лиса",
            "  - не можуть ходити, але лис не з'їв",
            "    7 гусей",
            "• Лис перемагає, якщо з'їсть 7 або",
            "  більше гусей"
        ]

        for rule in rules_text:
            text = self.small_font.render(rule, True, BLACK) #створює графічну поверхню
            text_rect = text.get_rect(left=sidebar_x + text_margin, top=current_y) #горизонтальну позиція #вертикальну позиція
            self.screen.blit(text, text_rect)
            current_y += line_spacing * 0.8

        #Повідомлення про можливість почати нову гру при завершенні поточної
        if self.game_state != GameState.PLAYING:
            current_y += line_spacing
            restart_text = "Натисніть ПРОБІЛ для нової гри"
            text = self.small_font.render(restart_text, True, BLACK)  #створює графічну поверхню
            text_rect = text.get_rect(center=(BOARD_SIZE + SIDEBAR_WIDTH // 2, current_y))
            self.screen.blit(text, text_rect)

        # Повідомлення про перемогу
        if self.game_state != GameState.PLAYING:
            # Створюємо прямокутник для повідомлення
            msg_rect = pygame.Rect(sidebar_x, current_y + line_spacing,
                                   sidebar_width - 20, line_spacing * 2)
            pygame.draw.rect(self.screen, BOARD_LIGHT, msg_rect)
            pygame.draw.rect(self.screen, DARK_GREEN, msg_rect, 2)

            # Текст перемоги
            winner_text = "Лис переміг!" if self.game_state == GameState.FOX_WIN else "Гуси перемогли!"
            text = self.font.render(winner_text, True, BLACK)
            text_rect = text.get_rect(center=(sidebar_x + sidebar_width // 2 - 10,
                                              current_y + line_spacing * 1.5))
            self.screen.blit(text, text_rect)

            # Інструкція для нової гри
            restart_text = "Натисніть ПРОБІЛ для нової гри"
            text = self.small_font.render(restart_text, True, BLACK)
            text_rect = text.get_rect(center=(sidebar_x + sidebar_width // 2 - 10,
                                              current_y + line_spacing * 2.2))
            self.screen.blit(text, text_rect)

    def draw_menu(self):
        """Малювання головного меню"""
        self.screen.fill(SIDEBAR_GREEN)

        # Заголовок
        title = self.font.render("Лис та гуси", True, BLACK) #створює текстову поверхню
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4)) #отримує прямокутник
        self.screen.blit(title, title_rect)

        # Кнопки
        for button in self.buttons:
            pygame.draw.rect(self.screen, BOARD_DARK, button['rect'], border_radius=10)  #координати та розміри прямокутника кнопки
            pygame.draw.rect(self.screen, BLACK, button['rect'], 2, border_radius=10) #малювання обводки кнопки

            text = self.font.render(button['text'], True, WHITE)
            text_rect = text.get_rect(center=button['rect'].center)
            self.screen.blit(text, text_rect)

    def _create_menu_buttons(self):
        """Створення кнопок меню"""
        buttons = []
        y_pos = WINDOW_HEIGHT // 3
        for mode in GameMode:
            buttons.append({
                'rect': pygame.Rect(WINDOW_WIDTH // 4, y_pos, WINDOW_WIDTH // 2, 50), #позиція та розмір кнопки
                'text': mode.value, #текст
                'mode': mode #режим гри
            })
            y_pos += 80
        return buttons

    def handle_menu_click(self, pos):
        """Обробка кліків у меню"""
        for button in self.buttons:
            if button['rect'].collidepoint(pos): #перевіряє, чи координати кліку (pos) потрапляють у межі прямокутника кнопки (rect)
                self.game_mode = button['mode']
                self.show_menu = False
                self.reset_game()
                if self.game_mode == GameMode.PVE_GEESE:
                    self.ai = AI(self, 2)  # ШІ грає за лиса
                elif self.game_mode == GameMode.PVE_FOX:
                    self.ai = AI(self, 1)  # ШІ грає за гусей

    def handle_keyboard(self, event):
        """Обробка клавіатурного вводу"""
        if event.key == pygame.K_ESCAPE:
            self.show_menu = True
        elif event.key == pygame.K_SPACE and self.game_state != GameState.PLAYING:
            self.show_menu = True
        elif event.key == pygame.K_r:
            self.reset_game() #повністю перезапускає гру

    def draw(self):
        """Малювання всієї гри"""
        if self.show_menu:
            self.draw_menu()
        else:
            self.draw_board()
            self.draw_highlights()
            self.draw_pieces()
            self.draw_sidebar()
        pygame.display.flip() #Оновлює весь екран


def main():
    """Головна функція гри"""
    game = Game()
    clock = pygame.time.Clock() #дозволяє контролювати швидкість гри

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: #кнопка закриття вікна
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.show_menu:
                    game.handle_menu_click(event.pos) #обробляємо вибір користувача з меню
                elif game.game_state == GameState.PLAYING:
                    game.handle_click(event.pos) #обробляємо клік миші в контексті гри

            elif event.type == pygame.KEYDOWN:
                game.handle_keyboard(event) #бробки клавіатурних команд

        game.update()
        game.draw()
        clock.tick(60) # встановлює максимальну кількість кадрів на секунду


if __name__ == "__main__":
    main()