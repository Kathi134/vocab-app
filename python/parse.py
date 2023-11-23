from logic import Score
from logic import FilterOptions

class Word:
    def __init__(self, german, spanish, grammar, comment, score: int =0, reverse_score: int =0, current_wrongs=0, archived=False):
        self.german: str = german
        self.spanish: str = spanish
        self.grammar: str = grammar
        self.comment: str = comment
        self.archived: bool = archived
        self.score: int = score
        self.reverse_score: int = reverse_score
        self.current_wrongs: int = current_wrongs

    def archive(self):
        self.archived = True

    def guessed(self, correct: bool):
        if correct:
            self.score += 1
        else:
            if self.current_wrongs == 2:
                self.score = 0 if self.score <= 1 else self.score-1
                self.current_wrongs = 0
            else:
                self.current_wrongs += 1

    def set_all(self, other):
        self.german = other.german
        self.spanish = other.spanish
        self.grammar = other.grammar
        self.comment = other.comment
        self.archived = other.archived
        self.score = other.score
        self.reverse_score = other.reverse_score
        self.current_wrongs: other.current_wrongs

    @staticmethod
    def empty():
        return Word("", "", "", "")

    def __eq__(self, other):
        return self.german.lower() == other.german.lower() \
               and self.spanish.lower() == other.spanish.lower()

    def deep_eq(self, other):
        return self.german == other.german \
            and self.spanish == other.spanish \
            and self.grammar == other.grammar \
            and self.comment == other.comment \
            and self.archived == other.archived \
            and self.score == other.score \
            and self.reverse_score == other.reverse_score \
            and self.current_wrongs == other.current_wrongs

    def __str__(self):
        return f"German: {self.german}, Spanish: {self.spanish}, Grammar: {self.grammar}, " \
               f"Comment: {self.comment}, Archived: {self.archived}, Score: {self.score}, " \
               f"Reverse-Score: {self.reverse_score}, Current-Wrongs: {self.current_wrongs}"


class Parser:
    def __init__(self, input_path, score_path, options_path):
        self.vocab_path = input_path
        self.score_path = score_path
        self.options_path = options_path

    def parse_vocab_input(self):
        words = []
        with open(self.vocab_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            header = None
            for line in lines:
                line = line.strip()
                if line.startswith("|") and line.endswith("|"):
                    parts = line[1:-1].split("|")
                    if header is None:
                        header = parts
                    elif all(item == "-" for item in parts):
                        continue
                    else:
                        if len(parts) == len(header):
                            german = parts[header.index("alemán")].strip()
                            spanish = parts[header.index("español")].strip()
                            grammar = parts[header.index("grammar")].strip()
                            comment = parts[header.index("fuente")].strip()
                            archived = "x" in parts[header.index("archived")]
                            score_txt = parts[header.index("score")]
                            score = int(score_txt) if score_txt.isnumeric() else 0
                            rev_score_txt = parts[header.index("reverse")]
                            reverse_score = int(rev_score_txt) if rev_score_txt.isnumeric() else 0
                            curr_wrongs_txt = parts[header.index("wrongs")]
                            curr_wrongs = int(curr_wrongs_txt) if curr_wrongs_txt.isnumeric() else 0
                            words.append(Word(german, spanish, grammar, comment, score, reverse_score, curr_wrongs, archived))
                        else:
                            print("Skipping invalid line:", line)
                else:
                    header = None

        return words

    def write_vocab(self, word_list: list[Word]):
        out = "|alemán|español|grammar|fuente|archived|score|reverse|wrongs|\n|-|-|-|-|-|-|-|-|\n"
        for word in word_list:
            s = str(word.score)
            r = str(word.reverse_score)
            w = str(word.current_wrongs)
            a = 'x' if word.archived else ''
            out += f"|{word.german}|{word.spanish}|{word.grammar}|{word.comment}|{a}|{s}|{r}|{w}|\n"
        with open(self.vocab_path, "w", encoding='utf-8') as file:
            file.write(out)

    def parse_score(self):
        with open(self.score_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if len(lines) == 0:
                lines = ["0 0"]
            games_played = int(lines[0].split(" ")[0])
            global_score = int(lines[0].split(" ")[1])

            return Score(games_played, global_score)

    def write_score(self, score):
        out = score.__str__()
        with open(self.score_path, "w", encoding='utf-8') as file:
            file.write(out)

    def write_options(self, options):
        out = options.__str__()
        with open(self.options_path, "w", encoding='utf-8') as file:
            file.write(out)

    def parse_options(self):
        with open(self.options_path, 'r', encoding='utf-8') as file:
            line = file.readline()
            if not line or line == "":
                line = FilterOptions().__str__()
            obj = {pair.split(':')[0].strip(): pair.split(':')[1].strip() == 'True' for pair in line.split(',')}
            return FilterOptions(**obj)
