import datetime
import platform
import subprocess
import sys
from types import NoneType

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, \
    QTabWidget, QTextEdit, QCheckBox, QFormLayout, QTableWidget, \
    QTableWidgetItem, QMessageBox, QSizePolicy, QLayout, QDialog

import api
from logic import Logic
from parse import Word, Parser


class VocabularyApp(QWidget):
    def __init__(self, parser, git_response):
        super().__init__()
        self.parser = parser

        whole_word_list: list[Word] = parser.parse_vocab_input()
        # whole_word_list = [Word("foo", "bar", "", "d"), Word("fnord", ",zilch ", "", "b"), Word("georg", "köhler", "", "u")]
        score = parser.parse_score()
        options = parser.parse_options()
        self.logic = Logic(score, whole_word_list, options)

        self.init_ui()

        if git_response.returncode != 0:
            QMessageBox.information(self, "Git Issue", f"There might be a problem with updating your files.\nSee exception below:\n\n{git_response.stderr}")

    def init_ui(self):
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle("Vocabulary Training App")
        self.current_idx = -1

        self.tabs = QTabWidget()

        # Tab 1: Add Words
        tab_add_words = QWidget()
        self.init_add_words_tab(tab_add_words)

        # Tab 2: Learning Interface
        tab_learning = QWidget()
        self.init_learning_tab(tab_learning)

        # Tab 3: Word List
        tab_word_list = QWidget()
        self.init_word_list_tab(tab_word_list)

        self.tabs.addTab(tab_add_words, "Add Words")
        self.tabs.addTab(tab_learning, "Learning")
        self.tabs.addTab(tab_word_list, "Word List")
        self.tabs.setCurrentIndex(1)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        # Connect the tab's focus event to update the word list when the tab is clicked
        self.tabs.currentChanged.connect(self.tab_changed)

        self.show()

    def tab_changed(self, new_tab_index):
        if new_tab_index == 2:
            self.update_word_list()
        elif new_tab_index == 1:
            self.logic.update_filtered_list()
            self.next_word()

    @staticmethod
    def hide_layout(layout):
        # Hide the layout and its contained widgets
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setHidden(True)

    def init_add_words_tab(self, tab):
        add_word_layout = QFormLayout()

        self.german_input = QLineEdit()
        self.spanish_input = QLineEdit()
        self.grammar_info_input = QLineEdit()
        self.comment_input = QTextEdit()

        add_button = QPushButton("Add Word")
        add_button.clicked.connect(self.add_word)

        add_word_layout.addRow("German:", self.german_input)
        add_word_layout.addRow("Spanish:", self.spanish_input)
        add_word_layout.addRow("Grammar Info:", self.grammar_info_input)

        self.default_comments_checkbox = QCheckBox("Keep value")
        self.default_comments_checkbox.setChecked(False)  # Set it unchecked by default
        comments_label_layout = QVBoxLayout()
        comments_label_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        comments_label = QLabel("Comment:")
        comments_label_layout.addWidget(comments_label)
        comments_label_layout.addWidget(self.default_comments_checkbox)
        container = QHBoxLayout()
        container.addLayout(comments_label_layout)
        container.addWidget(self.comment_input)
        add_word_layout.addRow(container)

        add_word_layout.addRow(add_button)

        tab.setLayout(add_word_layout)

        self.german_input.editingFinished.connect(self.auto_translate)
        self.german_input.focusInEvent = lambda e: self.unmark_field(self.german_input)
        self.spanish_input.focusInEvent = lambda e: self.unmark_field(self.spanish_input)

    def init_learning_tab(self, tab):
        learn_layout = QVBoxLayout()

        score_layout = QHBoxLayout()
        score_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)  # Set a fixed height for the score layout
        options_btn = QPushButton("☰")
        options_btn.setFixedWidth(25)
        self.global_score_label = QLabel(f"accuracy: {self.logic.get_accuracy():.2f}") # accuracy
        self.highest_level = QLabel(f"highest level: {self.logic.get_max_level()}")
        self.current_word_level = QLabel(f"current word's level: 0") # TODO: fix{self.current_word.score}")
        self.unleveled_words_label = QLabel(f"to go: {self.logic.get_words_to_learn()}")
        self.style_score_labels([self.global_score_label, self.highest_level, self.current_word_level, self.unleveled_words_label])
        stats_label = QLabel("🎯")
        stats_label.setFixedWidth(int(self.geometry().width() / 15))
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_layout.addWidget(stats_label)
        score_layout.addWidget(self.global_score_label)
        score_layout.addWidget(self.current_word_level)
        score_layout.addWidget(self.unleveled_words_label)
        score_layout.addWidget(self.highest_level)
        score_layout.addWidget(options_btn)
        learn_layout.addLayout(score_layout)

        self.flash_card = QLabel("")
        self.flash_card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.flash_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        learn_layout.addWidget(self.flash_card)

        self.grammar_label = QLabel("")
        self.grammar_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.grammar_label.setHidden(True)
        learn_layout.addWidget(self.grammar_label)

        help = "ñ (alt+164), ¿ (alt+168), ¡ (alt+173)"
        self.type_help = QLabel("🛈")
        self.type_help.setToolTip(help)
        learn_layout.addWidget(self.type_help)

        self.feedback_layout = QHBoxLayout()
        self.feedback = QLabel("")
        self.feedback.setFixedWidth(384)
        self.feedback_layout.addWidget(self.feedback)
        self.archive_button = QPushButton("Archive Word")
        self.feedback_layout.addWidget(self.archive_button)
        next_word_button = QPushButton("Next Word")
        self.feedback_layout.addWidget(next_word_button)
        self.hide_feedback_form()
        learn_layout.addLayout(self.feedback_layout)

        answer_layout = QHBoxLayout()
        self.user_input = QLineEdit("")
        self.user_input.setPlaceholderText("Type your answer here")
        answer_layout.addWidget(self.user_input)
        check_button = QPushButton("Check Answer")
        skip_button = QPushButton("Skip")
        answer_layout.addWidget(check_button)
        answer_layout.addWidget(skip_button)
        learn_layout.addLayout(answer_layout)

        options_btn.clicked.connect(self.init_options)
        self.user_input.focusInEvent = lambda e: self.unmark_field(self.user_input)
        check_button.clicked.connect(self.check_answer)
        next_word_button.clicked.connect(self.next_word)
        skip_button.clicked.connect(self.skip_word)
        self.archive_button.clicked.connect(self.archive_current_word)

        tab.setLayout(learn_layout)

        # Initialize the flash card with the first word
        self.next_word()

    def style_score_labels(self, labels: list[QLabel]):
        for label in labels:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # label.setFont()

    def init_word_list_tab(self, tab):
        word_list_layout = QVBoxLayout()
        self.word_table = QTableWidget()
        self.word_table.setColumnCount(5)
        self.word_table.setHorizontalHeaderLabels(["German", "Spanish", "💡", "ℹ️", "🎖️"])

        table_width = self.word_table.horizontalHeader().viewport().width() - 165
        self.word_table.setColumnWidth(0, int(table_width * 0.3))  # 30% for German
        self.word_table.setColumnWidth(1, int(table_width * 0.3))  # 30% for Spanish
        self.word_table.setColumnWidth(2, int(table_width * 0.3))  # 20% for Grammar
        self.word_table.setColumnWidth(3, 1)  # int(table_width * 0.025))  # 20% for Comment
        self.word_table.setColumnWidth(4, 1)  # int(table_width * 0.025))  # 20% for Comment
        self.word_table.cellPressed.connect(self.cell_selected)  # Connect cell selection event
        word_list_layout.addWidget(self.word_table)

        self.archive_selection_btn = QPushButton("De/Archive Selected Word")
        self.delete_btn = QPushButton("Delete Selected Word")
        edit_button = QPushButton("Enable Edit")
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.archive_selection_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        word_list_layout.addLayout(button_layout)

        filter_layout = QHBoxLayout()
        self.show_archived_checkbox = QCheckBox("Show Archived Words")
        self.search_input = QLineEdit()
        self.show_archived_checkbox.stateChanged.connect(self.update_word_list)
        self.search_input.textChanged.connect(self.update_word_list)

        filter_layout.addWidget(self.show_archived_checkbox)
        filter_layout.addWidget(self.search_input)
        word_list_layout.addLayout(filter_layout)

        tab.setLayout(word_list_layout)

        # Connect the button actions
        self.archive_selection_btn.clicked.connect(self.archive_selection)
        self.delete_btn.clicked.connect(self.delete_selection)
        edit_button.clicked.connect(self.enable_edit)
        save_button.clicked.connect(self.save_changes)
        cancel_button.clicked.connect(self.cancel_changes)

        # Create a temporary storage for changes
        self.edit_enabled = False  # Track if editing is enabled
        self.currently_editing = None  # Track the currently editing cell

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            tab = self.tabs.currentIndex()
            if tab == 0:
                self.add_word()
            elif tab == 2 and self.edit_enabled and self.currently_editing:
                self.save_changes()
            elif tab == 1 and not self.feedback.isVisible():
                self.check_answer()
            elif tab == 1 and self.feedback.isVisible():
                self.next_word()

    # tab add words

    def add_word(self):
        german = self.german_input.text()
        spanish = self.spanish_input.text()

        if not german:
            self.mark_field(self.german_input)
        if not spanish:
            self.mark_field(self.spanish_input)
        if not german or not spanish:
            return

        word = Word(german, spanish, self.grammar_info_input.text(), self.comment_input.toPlainText())
        if self.logic.word_in_list(word):
            QMessageBox.information(self, "Word Already in List", "The word is already in the list.")
        else:
            self.logic.add_word_to_list(word)
            self.parser.write_vocab(self.logic.word_list)
            print("Word added:", word)

        # Clear all fields and unmark them
        self.german_input.clear()
        self.spanish_input.clear()
        self.grammar_info_input.clear()
        self.unmark_field(self.german_input)
        self.unmark_field(self.spanish_input)
        if not self.default_comments_checkbox.isChecked():
            self.comment_input.clear()

    def mark_field(self, field):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 200, 200))
        field.setPalette(palette)

    def unmark_field(self, field):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        field.setPalette(palette)

    def auto_translate(self):
        if len(self.spanish_input.text()) == 0:
            translated_text = api.translate(self.german_input.text())
            self.spanish_input.setText(translated_text[1])

    # section learning options

    def init_options(self):
        options_dialog = QDialog(self)
        options_dialog.setWindowTitle("Learning Options")

        form_layout = QFormLayout()

        # Language direction section
        lang_direction_group = QWidget()
        lang_direction_layout = QVBoxLayout()
        self.ger_to_esp_checkbox = QCheckBox("German to Spanish")
        self.ger_to_esp_checkbox.setChecked(self.logic.filter_options.option_ger_to_esp)
        self.esp_to_ger_checkbox = QCheckBox("Spanish to German")
        self.esp_to_ger_checkbox.setChecked(self.logic.filter_options.option_esp_to_ger)
        lang_direction_layout.addWidget(self.ger_to_esp_checkbox)
        lang_direction_layout.addWidget(self.esp_to_ger_checkbox)
        lang_direction_group.setLayout(lang_direction_layout)
        form_layout.addRow("Language Direction:", lang_direction_group)

        # Filter section
        filter_group = QWidget()
        filter_layout = QVBoxLayout()
        self.filter_d_checkbox = QCheckBox("'d' (duolingo)")
        self.filter_b_checkbox = QCheckBox("'b' (book)")
        self.filter_u_checkbox = QCheckBox("'u' (uni-lesson)")
        self.filter_d_checkbox.setChecked(self.logic.filter_options.include_d)
        self.filter_u_checkbox.setChecked(self.logic.filter_options.include_u)
        self.filter_b_checkbox.setChecked(self.logic.filter_options.include_b)
        filter_layout.addWidget(self.filter_d_checkbox)
        filter_layout.addWidget(self.filter_b_checkbox)
        filter_layout.addWidget(self.filter_u_checkbox)
        filter_group.setLayout(filter_layout)
        form_layout.addRow("Included Words:", filter_group)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_options(options_dialog))

        form_layout.addWidget(save_button)

        options_dialog.setLayout(form_layout)
        options_dialog.exec()

    def save_options(self, dialog):
        # Validate input
        if not self.ger_to_esp_checkbox.isChecked() and not self.esp_to_ger_checkbox.isChecked():
            QMessageBox.critical(dialog, "Validation Error", "Please select at least one language direction.")
        elif self.esp_to_ger_checkbox.isChecked():
            QMessageBox.critical(dialog, "Validation Error", "Spanish to German is not implemented yet.")
        else:
            # Form is valid
            self.logic.filter_options.option_ger_to_esp = self.ger_to_esp_checkbox.isChecked()
            self.logic.filter_options.option_esp_to_ger = self.esp_to_ger_checkbox.isChecked()
            self.logic.filter_options.include_d = self.filter_d_checkbox.isChecked()
            self.logic.filter_options.include_b = self.filter_b_checkbox.isChecked()
            self.logic.filter_options.include_u = self.filter_u_checkbox.isChecked()
            self.parser.write_options(self.logic.filter_options)
            self.logic.update_filtered_list()
            self.next_word()
            dialog.accept()


    # tab learn

    def show_feedback_form(self):
        for i in range(self.feedback_layout.count()):
            self.feedback_layout.itemAt(i).widget().setHidden(False)
        self.grammar_label.setText(self.current_word.grammar)
        self.grammar_label.setHidden(False)
        self.type_help.setHidden(True)

    def hide_feedback_form(self):
        for i in range(self.feedback_layout.count()):
            self.feedback_layout.itemAt(i).widget().setHidden(True)
        self.grammar_label.setHidden(True)
        self.type_help.setHidden(False)

    def skip_word(self):
        self.check_answer(True)

    def next_word(self):
        self.hide_feedback_form()
        self.user_input.clear()
        self.archive_button.setHidden(True)
        # logic
        if not self.logic.any_word_in_filtered_list():
            self.current_word = Word.empty()
        else:
            idx = self.logic.get_suitable_random()
            self.current_word = self.logic.filtered_list[idx]
            # self.current_idx = self.whole_word_list.index(self.current_word)
            self.update_score_view()
        self.flash_card.setText(self.current_word.german)

    def check_answer(self, skip=False):
        input = self.user_input.text()
        if not skip and input.strip() == "":
            self.mark_field(self.user_input)
            return
        self.logic.add_one_played_game()
        self.parser.write_score(self.logic.score)
        self.show_feedback_form()
        if self.logic.check_answer(self.current_word.spanish, input):
            self.feedback.setText(f"CORRECT.✔️ ({self.current_word.spanish})")
            self.current_word.score += 1
        else:
            self.feedback.setText(f"FALSE.❌ Solution: {self.current_word.spanish}")
            self.archive_button.setHidden(True)
        self.parser.write_vocab(self.logic.word_list)

    def update_score_view(self):
        self.global_score_label.setText(f"accuracy: {self.logic.get_accuracy():.2f}")
        self.highest_level.setText(f"highest level: {self.logic.get_max_level()}")
        self.current_word_level.setText(f"current word's level: {self.current_word.score}")
        self.unleveled_words_label.setText(f"to go: {self.logic.get_words_to_learn()}")

    def archive_current_word(self):
        self.current_word.archive()
        self.parser.write_vocab(self.logic.word_list)
        self.feedback.setText("CORRECT.✔️ Word is now archived.")

    # tab word list

    def update_word_list(self):
        # Clear the table
        self.word_table.setRowCount(0)

        search_term = self.search_input.text().lower()
        show_archived = self.show_archived_checkbox.isChecked()

        filtered_archive_list = self.logic.list_words_depending_if_show_archived(show_archived)
        self.archive_selection_btn.setText(f"{'Dearchive' if show_archived else 'Archive'} selected word")

        i = -1
        for word in filtered_archive_list:
            i += 1
            if search_term not in word.german.lower() and search_term not in word.spanish.lower():
                continue
            row_position = self.word_table.rowCount()
            self.word_table.insertRow(row_position)
            self.word_table.setItem(row_position, 0, QTableWidgetItem(word.german))
            self.word_table.setItem(row_position, 1, QTableWidgetItem(word.spanish))
            self.word_table.setItem(row_position, 2, QTableWidgetItem(word.grammar))
            self.word_table.setItem(row_position, 3, QTableWidgetItem(word.comment))
            self.word_table.setItem(row_position, 4, QTableWidgetItem(str(word.score)))
        self.disable_edit()
        self.cell_selected(-1, -1)

    def enable_edit(self):
        # Enable cell editing when the "Enable Edit" button is clicked
        if self.currently_editing != (-1, -1) and self.currently_editing[1] not in [4, 5]:
            item = self.word_table.item(self.currently_editing[0], self.currently_editing[1])
            if item:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.word_table.editItem(item)
                self.edit_enabled = True

    def disable_edit(self):
        for row in range(self.word_table.rowCount()):
            for col in range(self.word_table.columnCount()):
                item = self.word_table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def save_changes(self):
        if type(self.matching_index) == NoneType:
            QMessageBox.critical(self, "Save Error", "Please only edit one cell at a time.")
        elif self.edit_enabled and self.currently_editing != (-1, -1):
            item = self.word_table.item(self.currently_editing[0], self.currently_editing[1])
            word = self.logic.get_word_at_index(self.matching_index)
            self.change_value(word, item.text())
            self.parser.write_vocab(self.logic.word_list)

        self.edit_enabled = False  # Disable editing after saving
        self.update_word_list()

    def change_value(self, word: Word, new_value):
        idx = self.currently_editing[1]
        if idx == 0:
            word.german = new_value
        elif idx == 1:
            word.spanish = new_value
        elif idx == 2:
            word.grammar = new_value
        elif idx == 3:
            word.comment = new_value

    def cancel_changes(self):
        # Discard changes made in edit mode
        self.edit_enabled = False  # Disable editing after canceling
        self.update_word_list()

    # Connect the table cell selection event to track the currently selected cell
    def cell_selected(self, row, col):
        self.currently_editing = (row, col)
        print(self.currently_editing)
        cell_contents = []
        for i in range(self.word_table.columnCount()):
            item = self.word_table.item(row, i)
            cell_contents.append(item.text() if item else '')

        # Search for a matching item in word_list
        matching_index = None
        for index, word in enumerate(self.logic.word_list):
            if (word.german, word.spanish, word.grammar, word.comment) == tuple(cell_contents[0:4]):
                matching_index = index
                break

        # Store the matching index
        self.matching_index = matching_index

    def delete_selection(self):
        # TODO: fix - sth wrong is deleted
        if self.currently_editing != (-1, -1):
            w = self.logic.word_list[self.matching_index]
            self.show_delete_confirmation(f"{w.german} - {w.spanish}")
            self.update_word_list()

    def show_delete_confirmation(self, word):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Delete Confirmation")
        msg_box.setText(f"Really delete '{word}'?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        result = msg_box.exec()

        if result == QMessageBox.StandardButton.Ok:
            self.logic.delete_word_at_idx(self.matching_index)
            self.parser.write_vocab(self.logic.word_list)
        else:
            self.cancel_changes()

    def archive_selection(self):
        if self.currently_editing != (-1, -1):
            if self.show_archived_checkbox.isChecked():
                print("dearchiving " + self.logic.word_list[self.matching_index].german)
                self.logic.dearchive_word_at_index(self.matching_index)
            else:
                print("archiving " + self.logic.word_list[self.matching_index].german)
                self.logic.archive_word_at_index(self.matching_index)

            self.parser.write_vocab(self.logic.word_list)
            self.update_word_list()


def git_pull():
    print("git pull")
    pull_process = subprocess.run(["git","pull"], capture_output=True, text=True)
    return pull_process

def git_push():
    print("git add .\\vocabs-python.md")
    res = subprocess.run(["git","add", "vocabs-python.md"], capture_output=True, text=True)
    if res.returncode != 0:
        print("\t", res.stdout, res.stderr)
    print("git add .\\score.txt")
    res = subprocess.run(["git","add", "score-python.txt"], capture_output=True, text=True)
    if res.returncode != 0:
        print("\t", res.stdout, res.stderr)
    host = platform.node()
    date = datetime.datetime.now()
    formatted_time = date.strftime("%d-%m-%y, %H:%M")
    commit_msg = f"\"vocab-app update: from {host}, {formatted_time}\""
    print(f"git commit -m {commit_msg}")
    res = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
    if res.returncode != 0:
        print("\t", res.stdout, res.stderr)
    print("git push")
    res = subprocess.run(["git", "push"], capture_output=True, text=True)
    if res.returncode != 0:
        print("\t", res.stdout, res.stderr)


if __name__ == '__main__':
    git_response = git_pull()
    markdown_file_path = r'.\vocabs-python.md'
    score_file_path = r'.\score-python.txt'
    options_file_path = r'.\internal-python.txt'
    app = QApplication(sys.argv)
    window = VocabularyApp(Parser(markdown_file_path, score_file_path, options_file_path), git_response)
    exit_code = app.exec()
    git_push()
    sys.exit(exit_code)

