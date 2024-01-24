import random

def print_state(state):
    """
    Prints the state in a readable format.
    """

    for hypothesis in state:
        hypothesis_str = "".join(["R" if x else "B" for x in hypothesis])
        print(hypothesis_str, state[hypothesis])
    print()

def generate_missions(player_count, participant_count):
    """
        Generates all possible configurations of participants on a mission.
    """
    possible_participants = []
    for i in range(2**player_count):
        participants = []
        for j in range(player_count):
            if i & (1 << j):
                participants.append(j)
        if len(participants) == participant_count:
            possible_participants.append(participants)

    return possible_participants

def can_play_fail(mission_number, participants, hypothesis):
    """
    Checks if the hypothesis allows the participants to play fail on the mission.

    NOTE: In 7 player game, the 4th mission requires 2 fails so this function needs to be modified if the number of players changes.
    """

    spy_count = sum([1 if hypothesis[participant] else 0 for participant in participants])
   # print(participants, hypothesis, spy_count)
    
    if mission_number == 4: 
        return spy_count >= 2
    else:
        return spy_count >= 1

def prob_fail(mission_number, participants, hypothesis, results, spy_params):
    """
        Returns the probability of the mission failing given the participants and the hypothesis. 
        The probability is calculated using the spy parameters which take into accound
            1. The number of the mission
            2. The number of spies on the mission
            3. The number of successes so far
        If there are not enough spies to play fail, the probability is 0.
        If playing success loses the game for spies, the spies will play fail. The same is true if playing fail wins the game for spies.
    """

   # print("hypothesis: ", hypothesis)
    if not can_play_fail(mission_number, participants, hypothesis):
        return 0

    successess = sum([1 - result for result in results])
    fails = len(results) - successess

    if successess == 2:
        return 1
    if fails == 2:
        return 1

    spy_count = sum([1 if hypothesis[participant] else 0 for participant in participants])

    return spy_params[(mission_number, spy_count, successess)]

def prob_success(mission_number, participants, hypothesis, results, spy_params):
    """
        Returns the probability of success given the participants and the hypothesis.
    """

    return 1 - prob_fail(mission_number, participants, hypothesis, results, spy_params)

def update_mission_fail(mission_number, participants, state_original, results, spy_params):
    """
        Updates the state if a mission fails.

        This is done using the Bayes' theorem. The function first calculates the probability of the mission failing given the participants
        and the hypothesis. Then it multiplies the probability with the 
    """

    state = dict(state_original)
    total = 0
    for hypothesis in state:
        state[hypothesis] = prob_fail(mission_number, participants, hypothesis, results, spy_params) * state[hypothesis]
        total += state[hypothesis]
    
    if total <= 10**(-6):
        return state
    
    for hypothesis in state:
        state[hypothesis] /= total
    
    return state

def update_mission_success(mission_number, participants, state_original, results, spy_params):
    """
        Updates the state if a mission fails. The function works similarly to update_mission_fail.
    """

    state = dict(state_original)
    total = 0
    for hypothesis in state:
        state[hypothesis] = prob_success(mission_number, participants, hypothesis, results, spy_params) * state[hypothesis]
        total += state[hypothesis]

    if total <= 10**(-6):
        return state

    for hypothesis in state:
        state[hypothesis] /= total
    
    return state

def chance_to_win(round_number, results_original, state_original, spy_params):
    """
        The main function of the program. It calculates the chance of winning the game given the results so far and the current state.

        The function works recursively. 
            - If either there are 3 successes or 3 fails, the function returns 1 or 0 respectively. 
            - If current round is 5
        (the last round), the function returns the probability of the hypothesis with the highest probability (this is done because in the last round
        the mission has to have all players except the spies to succeed. Thus they have to choose correctly, who the spies are and that is the hypothesis with
        the highest probability). )
            - Otherwise the function loops through all possible configurations of participants on the mission and calculates the probability of win 
            if the participants are chosen. The probability is calculated by first calculating the probability of winning the game if the mission succeeds (P(win | success))
            and the probability of winning the game if the mission fails (P(win | fail)). The probability of mission succeeding (P(success)) is calculated by looping trough all 
            hypotheses and calculating the probability of the mission succeeding given the hypothesis (P(success | hypothesis)) and multiplying it 
            with the probability of the hypothesis (P(hypothesis)). The probability of failure is calculated with P(fail) = 1 - P(success). 
            The probability of winning the game with these participants is then P(win | participants) = P(success) * P(win | success) + P(fail) * P(win | fail).

    """
    state = dict(state_original)
    results = list(results_original)

    successes = sum(results)
    fails = len(results) - successes

    if successes == 3:
        return 1
    if fails == 3:
        return 0

    if round_number == 5:
       # print("5", max(state.values()))
        return max(state.values())

    max_chance = 0
    if round_number == 1:
        possible_participants = [[0,1]]
    elif round_number == 2:
        possible_participants = [[0,1,2], [0,2,3], [3,4,5]]
    else:
        people_on_mission = [2, 3, 3, 4, 4][round_number - 1]
        possible_participants = generate_missions(7, people_on_mission)

    for participants in possible_participants:
        state_after_success = update_mission_success(round_number, participants, state, results, spy_params)
        results_after_success = results + [1]
        chance_after_success = chance_to_win(round_number + 1, results_after_success, state_after_success, spy_params)
        
        #if round_number == 3:
        #    print("stuff: ", results, [state_after_success[x] for x in state_after_success])

        state_after_fail = update_mission_fail(round_number, participants, state, results, spy_params)
        results_after_fail = results + [0]
        chance_after_fail = chance_to_win(round_number + 1, results_after_fail, state_after_fail, spy_params)

        chance_of_success = 0
        for hypothesis in state:
            chance_of_success += state[hypothesis] * prob_success(round_number, participants, hypothesis, results, spy_params)    

        chance = chance_of_success * chance_after_success + (1 - chance_of_success) * chance_after_fail
        #if round_number == 2:
        #    print(results, participants, chance)
        max_chance = max(max_chance, chance)
    return max_chance

def chance_to_win2(round_number, results_original, state_original_belief, state_original_real, spy_params_belief, spy_params_real):

    state_belief = dict(state_original_belief)
    state_real = dict(state_original_real)
    results = list(results_original)

    successes = sum(results)
    fails = len(results) - successes

    if successes == 3:
        return 1
    if fails == 3:
        return 0

    if round_number == 5:
       # print("5", max(state.values()))
#        print("max real: ", state_real[max(state_belief, key=state_belief.get)], "max belief: ", state_belief[max(state_belief, key=state_belief.get)])
        return state_real[max(state_belief, key=state_belief.get)]

    max_chance_belief = 0
    played_chance_real = 0
    if round_number == 1:
        possible_participants = [[0,1]]
    elif round_number == 2:
        possible_participants = [[0,1,2], [0,2,3], [3,4,5]]
    else:
        people_on_mission = [2, 3, 3, 4, 4][round_number - 1]
        possible_participants = generate_missions(7, people_on_mission)

    for participants in possible_participants:
        state_after_success_belief = update_mission_success(round_number, participants, state_belief, results, spy_params_belief)
        state_after_success_real = update_mission_success(round_number, participants, state_real, results, spy_params_real)
        results_after_success = results + [1]
        chance_after_success_belief = chance_to_win(round_number + 1, results_after_success, state_after_success_belief, spy_params_belief)
        chance_after_success_real = chance_to_win2(round_number + 1, results_after_success, state_after_success_belief, state_after_success_real, spy_params_belief, spy_params_real)

        #if round_number == 3:
        #    print("stuff: ", results, [state_after_success[x] for x in state_after_success])

        state_after_fail_belief = update_mission_fail(round_number, participants, state_belief, results, spy_params_belief)
        state_after_fail_real = update_mission_fail(round_number, participants, state_real, results, spy_params_real)
        results_after_fail = results + [0]
        chance_after_fail_belief = chance_to_win(round_number + 1, results_after_fail, state_after_fail_belief, spy_params_belief)
        chance_after_fail_real = chance_to_win2(round_number + 1, results_after_fail, state_after_fail_belief, state_after_fail_real, spy_params_belief, spy_params_real)

        chance_of_success_belief = 0
        chance_of_success_real = 0
        for hypothesis in state_belief:
            chance_of_success_belief += state_belief[hypothesis] * prob_success(round_number, participants, hypothesis, results, spy_params_belief) 
            chance_of_success_real += state_real[hypothesis] * prob_success(round_number, participants, hypothesis, results, spy_params_real)

        chance_belief = chance_of_success_belief * chance_after_success_belief + (1 - chance_of_success_belief) * chance_after_fail_belief
        chance_real = chance_of_success_real * chance_after_success_real + (1 - chance_of_success_real) * chance_after_fail_real
        if chance_belief > max_chance_belief:
            max_chance_belief = chance_belief
            played_chance_real = chance_real

#        if round_number == 2:
#            print("belief: ",   results, participants, chance_belief)
#            print("real: ", results, participants, chance_real)
        max_chance_belief = max(max_chance_belief, chance_belief)

    return played_chance_real

def simulate_game_old(round_number, results_original, state_original, correct_hypothesis, spy_params):
    """
        Simulates the game. The function works similarly to chance_to_win but instead of calculating the probability of winning the game,
        it simulates the game by always taking the action that maximizes the chance of winning the game.

        The function returns True if the spies win and False otherwise.
    """
    
    state = dict(state_original)
    results = list(results_original)

    successes = sum(results)
    fails = len(results) - successes

    if successes == 3:
        return True
    if fails == 3:
        return False
    
    if round_number == 5:
        return max(state, key=state.get) == correct_hypothesis
    
    if round_number == 1:
        possible_participants = [[0,1]]
    elif round_number == 2:
        possible_participants = [[0,1,2], [0,2,3], [3,4,5]]
    else:
        people_on_mission = [2, 3, 3, 4, 4][round_number - 1]
        possible_participants = generate_missions(7, people_on_mission)
    
    best_chance = 0
    best_participants = []
    for participants in possible_participants:
        state_after_success = update_mission_success(round_number, participants, state, results, spy_params)
        results_after_success = results + [1]
        chance_after_success = chance_to_win(round_number + 1, results_after_success, state_after_success, spy_params)

        state_after_fail = update_mission_fail(round_number, participants, state, results, spy_params)
        results_after_fail = results + [0]
        chance_after_fail = chance_to_win(round_number + 1, results_after_fail, state_after_fail, spy_params)

        chance_of_success = 0
        for hypothesis in state:
            chance_of_success += state[hypothesis] * prob_success(round_number, participants, hypothesis, results, spy_params)
        chance = chance_of_success * chance_after_success + (1 - chance_of_success) * chance_after_fail

        if chance > best_chance:
            best_chance = chance
            best_participants = participants
    
    if random.random() < prob_success(round_number, best_participants, correct_hypothesis, results, spy_params):
        return simulate_game_old(round_number + 1, results + [1], update_mission_success(round_number, best_participants, state, results, spy_params), correct_hypothesis, spy_params)
    else:
        return simulate_game_old(round_number + 1, results + [0], update_mission_fail(round_number, best_participants, state, results, spy_params), correct_hypothesis, spy_params)

"""

DOESN'T WORK YET

def simulate_game(round_number, results_original, state_original_belief, state_original_real, correct_hypothesis, spy_params):
    
#        Simulates the game. The function works similarly to chance_to_win but instead of calculating the probability of winning the game,
#        it simulates the game by always taking the action that maximizes the chance of winning the game.

#       The function returns True if the spies win and False otherwise.
    
    state_belief = dict(state_original_belief)
    results = list(results_original)

    successes = sum(results)
    fails = len(results) - successes

    if successes == 3:
        return True
    if fails == 3:
        return False
    
    if round_number == 5:
        return max(state_belief, key=state.get) == correct_hypothesis
    
    if round_number == 1:
        possible_participants = [[0,1]]
    elif round_number == 2:
        possible_participants = [[0,1,2], [0,2,3], [3,4,5]]
    else:
        people_on_mission = [2, 3, 3, 4, 4][round_number - 1]
        possible_participants = generate_missions(7, people_on_mission)
    
    best_chance = 0
    best_participants = []
    for participants in possible_participants:
        state_belief_after_success = update_mission_success(round_number, participants, state_belief, results, spy_params)
        results_after_success = results + [1]
        chance_after_success = chance_to_win(round_number + 1, results_after_success, state_belief_after_success, spy_params)

        state_belief_after_fail = update_mission_fail(round_number, participants, state_belief, results, spy_params)
        results_after_fail = results + [0]
        chance_after_fail = chance_to_win(round_number + 1, results_after_fail, state_belief_after_fail, spy_params)

        chance_of_success = 0
        for hypothesis in state_belief:
            chance_of_success += state_belief[hypothesis] * prob_success(round_number, participants, hypothesis, results, spy_params)
        chance = chance_of_success * chance_after_success + (1 - chance_of_success) * chance_after_fail

        if chance > best_chance:
            best_chance = chance
            best_participants = participants
    
    if random.random() < prob_success(round_number, best_participants, correct_hypothesis, results, spy_params):
        new_state_belief = update_mission_success(round_number, best_participants, state_belief, results, spy_params) 
        return simulate_game(round_number + 1, results + [1], new_state_belief, new_state_belief, correct_hypothesis, spy_params)
    else:
        new_state_belief = update_mission_fail(round_number, best_participants, state_belief, results, spy_params)
        return simulate_game(round_number + 1, results + [0], new_state_belief, new_state_belief, correct_hypothesis, spy_params)

"""


def init_state(player_count, number_of_spies):
    """
        Initializes the state.

        The state is a dictionary where the keys are the hypotheses and the values are the corresponding probabilities.
    """
    
    state = {}
    for i in range(2**player_count):
        hypothesis = [False] * player_count
        spy_count = 0
        for j in range(player_count):
            if i & (1 << j):
                hypothesis[j] = True
                spy_count += 1
        if spy_count == number_of_spies:
            state[tuple(hypothesis)] = 1
    
    for hypothesis in state:
        state[hypothesis] /= len(state)
    
    return state


def init_spy_params():
    """
        Initializes the spy parameters.

        The spy parameters are a dictionary where the keys are tuples (mission_number, spy_count, successess) and the values are the corresponding probabilities.
        The dictionary only has to contain the parameters for the missions where there is no trivial strategy (i.e. no 2 previous successes or fails and enough spies to play fail)
    """

    params = {
        (1, 1, 0): 0.2  ,
        (1, 2, 0): 0,
        (2, 1, 0): 1,
        (2, 1, 1): 1,
        (2, 2, 0): 1,
        (2, 2, 1): 1,
        (2, 3, 0): 1,
        (2, 3, 1): 1,
        (3, 1, 1): 1,
        (3, 2, 1): 1,
        (3, 3, 1): 1,
    }

    return params

def constant_params(constant):
    """
        Initializes the spy parameters with a constant value.
    """
    
    states = [(1,1,0),(1,2,0),(2,1,0),(2,1,1),(2,2,0),(2,2,1),(2,3,0),(2,3,1),(3,1,1),(3,2,1),(3,3,1)]
    return {state: constant for state in states}

def find_constant_param():
    """
        Finds the value of the constant parameter that gives the spies the highest chance of winning.
    """
    
    states = [(1,1,0),(1,2,0),(2,1,0),(2,1,1),(2,2,0),(2,2,1),(2,3,0),(2,3,1),(3,1,1),(3,2,1),(3,3,1)]
    for prob in range(1, 10):
        prob /= 10
        params = {state: prob for state in states}
        print(f"{prob}: {chance_to_win(1, [], init_state(7, 3), params)}")

state = init_state(7, 3)
spy_params_belief = constant_params(0.999)
spy_params_real = constant_params(0.5)

print("chance_to_win2: ", chance_to_win2(1, [], state, state, spy_params_belief, spy_params_real))

"""
def simulate_all_games(player_count, spy_count, num_games, spy_params_belief, spy_params_real):
#        Simulates all possible spy configurations num_games times and returns the average chance of winning.
    
    state = init_state(player_count, spy_count)
    chance = 0
    for hypothesis in state: 
        chance_to_win_hypothesis = 0
        
        for _ in range(num_games):
            if simulate_game(1, [], state, state, hypothesis, spy_params_belief):
                chance_to_win_hypothesis += 1

        chance_to_win_hypothesis /= num_games

        chance += chance_to_win_hypothesis
        print(hypothesis, chance_to_win_hypothesis)
    chance /= len(state)
    return chance"""