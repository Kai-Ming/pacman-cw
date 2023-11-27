# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util

class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!"
        name = "Pacman"
        
        self.reward = -1
        self.discount = 0.995
        self.food_utility = 20
        self.capsule_utility = 50
        self.ghost_utility = -1000000
        self.scared_ghost_utility = 200

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running registerInitialState for MDPAgent!"
        print "I'm at:"
        print api.whereAmI(state)
        
    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"

    # Returns the position of the next state given the current position and direction
    def forward(self, position, direction):
        if direction == Directions.NORTH:
            return (position[0], position[1] + 1)
        elif direction == Directions.SOUTH:
            return (position[0], position[1] - 1)
        elif direction == Directions.EAST:
            return (position[0] + 1, position[1])
        elif direction == Directions.WEST:
            return (position[0] - 1, position[1])
        else:
            return position
        
    # Returns a deep copy of the maze
    def copy(self, maze):
        columns = len(maze[0]) # x coordinate
        rows = len(maze) # y coordinate

        maze_copy = [[0 for x in range(columns)] for y in range(rows)]
        for y in range(rows):
            for x in range(columns):
                maze_copy[y][x] = maze[y][x]

        return maze_copy
    
    # Initializes the utility of each state in the maze
    def map(self, state):
        corners = api.corners(state)
        walls = api.walls(state)
        food = api.food(state)
        capsules = api.capsules(state)
        ghost = api.ghosts(state)
        scared_ghost = api.ghostStates(state)

        size = corners[len(corners) - 1]
        columns = size[0] + 1 # x coordinate 
        rows = size[1] + 1 # y coordinate

        maze = [[0 for x in range(columns)] for y in range(rows)]
        for y in range(rows):
            for x in range(columns):
                if (x, y) in walls:
                    maze[y][x] = None
                elif ((x, y), 1) in scared_ghost:
                    maze[y][x] = self.scared_ghost_utility
                elif (x, y) in ghost:
                    maze[y][x] = self.ghost_utility
                elif (x, y) in capsules:
                    maze[y][x] = self.capsule_utility
                elif (x, y) in food:
                    maze[y][x] = self.food_utility
                else:
                    maze[y][x] = 0

        return maze
    
    # Returns a list of tuples containing the positions of the states around the current state
    def nearby(self, position, maze):
        actions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        nearby = {}
        for action in actions:
            forward_position = self.forward(position, action)
            # There is a wall in front, so we can't move there
            if maze[forward_position[1]][forward_position[0]] is None:
                nearby[action] = position
            # The path is clear, so we can move there
            else:
                nearby[action] = forward_position
        return nearby
    
    # Determines if pacman is facing a wall
    def move(self, position, direction, maze):
        forward_position = self.forward(position, direction)
        if maze[forward_position[1]][forward_position[0]] is None:
            return False
        else:
            return True

    # Calculates the utility of a state
    def bellman(self, position, maze, state):
        ghosts = api.ghosts(state)
        food = api.food(state)
        capsules = api.capsules(state)
        scared_ghost = api.ghostStates(state)

        near = self.nearby(position, maze)

        utilities = []
        for key in near:
            # Gets the resulting position from going in the direction
            forward = near[key]
            right = near[Directions.RIGHT[key]]
            left = near[Directions.LEFT[key]]

            # Gets the utility of the state from going in the direction
            forward_utility = maze[forward[1]][forward[0]]
            right_utility = maze[right[1]][right[0]]
            left_utility = maze[left[1]][left[0]]

            # change reward to match the state youre facing
            reward = self.reward
            if (forward, 1) in scared_ghost:
                reward = self.scared_ghost_utility
            elif forward in ghosts:
                reward = self.ghost_utility
            elif forward in food:
                reward = self.food_utility
            elif forward in capsules:
                reward = self.capsule_utility

            utility = reward + self.discount * (0.8 * forward_utility + 0.1 * right_utility + 0.1 * left_utility)

            utilities.append(utility)

        # Returns the maximum utility
        return max(utilities)

    # Update the utility of each state in the maze
    def value_iteration(self, current_maze, state):
        ghosts = api.ghosts(state)
        next_maze = self.copy(current_maze)
    
        for y in range(len(current_maze)):
            for x in range(len(current_maze[0])):
                if current_maze[y][x] is not None and (x, y) not in ghosts:
                    # The state is not a wall or a ghost, update utility
                    next_maze[y][x] = self.bellman((x, y), current_maze, state)
    
        return next_maze
    
    """ def print_maze(self, maze):
        columns = len(maze[0]) # x coordinate
        rows = len(maze) # y coordinate

        for i in range(rows):
            for j in range(columns):
                # print grid elements with no newline
                print maze[rows - (i + 1)][j], "|",
            # A new line after each line of the grid
            print 
        # A line after the grid
        print """

    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        pacman = api.whereAmI(state)

        maze = self.map(state) # Initialize the maze

        # Perform value iteration on the maze over 20 iterations
        counter = 0
        while (counter < 20):
            counter = counter + 1  
            maze = self.value_iteration(maze, state) # Updates the utility of each state in the maze

        near = self.nearby(pacman, maze) # Gets the utilities of the immediate states around pacman
        max_utility = (float("-inf"), Directions.STOP) 

        # Picks the highest utility state
        for key in near:
            position = near[key]
            if self.move(pacman, key, maze):
                # The direction is not going towards a wall
                if maze[position[1]][position[0]] > max_utility[0]:
                    max_utility = (maze[position[1]][position[0]], key)

        # Moves to the state that has the highest utility near pacman
        return api.makeMove(max_utility[1], legal)
