import random


class Score:
    def __init__(self, games_played, global_score):
        self.games_played = games_played
        self.global_score = global_score

    def get_accuracy(self, word_list):
        if self.games_played == 0:
            return 0
        # sum of all scores -> rev and score
        games_that_scored = sum(
            [sum([word.score for word in word_list]), sum([word.reverse_score for word in word_list])])
        return games_that_scored / self.games_played

    def __str__(self):
        return f"{self.games_played} {self.global_score}"


class FilterOptions:
    def __init__(self, gte=True, etg=False, d=True, b=True, u=True, a=False):
        self.option_ger_to_esp = gte
        self.option_esp_to_ger = etg
        self.include_d = d
        self.include_b = b
        self.include_u = u
        self.include_archived = a

    def __str__(self):
        return f"gte:{self.option_ger_to_esp}, etg:{self.option_esp_to_ger}, u:{self.include_u}, " \
               f"b:{self.include_b}, d:{self.include_d}, a:{self.include_archived}"


class Logic:
    def __init__(self, score, word_list, filter_options):
        self.score = score
        self.word_list: list = word_list
        self.filter_options: FilterOptions = filter_options
        self.filtered_list: list = []

        self.update_filtered_list()

    def add_one_played_game(self):
        self.score.games_played += 1

    def get_suitable_random(self):
        min_s = self.get_min_level()
        max_s = self.get_max_level()
        if len(self.filtered_list) != 0:
            i = random.randint(0, len(self.filtered_list) - 1)
            while max_s != 0 and min_s != max_s and self.filtered_list[i].score != min_s:
                i = random.randint(0, len(self.filtered_list) - 1)
            return i
        return -1

    @staticmethod
    def check_answer(spanish_sol, user_input):
        sol_tokens = [token.strip().lower() for token in spanish_sol.split(",")]
        answer_tokens = [token.strip().lower() for token in user_input.split(",")]
        return all(token in sol_tokens for token in answer_tokens)

    def update_filtered_list(self):
        self.filtered_list = [word for word in self.word_list if
                              (self.filter_options.include_d or word.comment != "d") and
                              (self.filter_options.include_u or word.comment != "u") and
                              (self.filter_options.include_b or word.comment != "b") and
                              (self.filter_options.include_archived or not word.archived)]

    def word_in_list(self, word):
        return word in self.word_list

    def add_word_to_list(self, word):
        self.word_list.append(word)

    def any_word_in_filtered_list(self):
        return len(self.filtered_list) != 0

    def get_max_level(self):
        max_s = max([word.score for word in self.filtered_list])
        return max_s

    def get_min_level(self):
        min_s = min([word.score for word in self.filtered_list])
        return min_s

    def list_words_depending_if_show_archived(self, show_archived):
        return [w for w in self.word_list
                if (show_archived and w.archived) or (not show_archived and not w.archived)]

    def get_word_at_index(self, idx):
        return self.word_list[idx]

    def archive_word_at_index(self, idx):
        self.word_list[idx].archive()

    def dearchive_word_at_index(self, idx):
        self.word_list[idx].archived = False

    def delete_word_at_idx(self, idx):
        print("deleted", self.word_list.pop(idx))

    def get_accuracy(self):
        return self.score.get_accuracy(self.word_list)

    def get_words_to_learn(self):
        max = self.get_max_level()
        return [w for w in self.filtered_list if w.score != max].__len__()