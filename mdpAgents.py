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
    def map(self, state, food_utility, ghost_utility):
        corners = api.corners(state)
        walls = api.walls(state)
        food = api.food(state)
        ghost = api.ghosts(state)

        size = corners[len(corners) - 1]
        columns = size[0] + 1 # x coordinate 
        rows = size[1] + 1 # y coordinate

        maze = [[0 for x in range(columns)] for y in range(rows)]
        for y in range(rows):
            for x in range(columns):
                if (x, y) in walls:
                    maze[y][x] = None
                elif (x, y) in ghost:
                    maze[y][x] = ghost_utility
                elif (x, y) in food:
                    maze[y][x] = food_utility
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

    # Calculates the utility of a state
    def bellman(self, position, maze, reward, discount):
        near = self.nearby(position, maze)

        utilities = []
        for key in near:
            forward = near[key]
            right = near[Directions.RIGHT[key]]
            left = near[Directions.LEFT[key]]

            forward_utility = maze[forward[1]][forward[0]]
            right_utility = maze[right[1]][right[0]]
            left_utility = maze[left[1]][left[0]]

            util = reward + discount * (0.8 * forward_utility + 0.1 * right_utility + 0.1 * left_utility)
            utilities.append(util)

        # Returns the maximum utility
        return max(utilities)

    def value_iteration(self, current_maze, reward, discount):
        previous_maze = []
        while (previous_maze != current_maze):
            previous_maze = self.copy(current_maze)
            for y in range(len(current_maze)):
                for x in range(len(current_maze[0])):
                    if current_maze[y][x] is not None:
                        current_maze[y][x] = self.bellman((x, y), previous_maze, reward, discount)

        return current_maze
    
    def print_maze(self, maze):
        columns = len(maze[0]) # x coordinate
        rows = len(maze) # y coordinate

        for i in range(rows):
            for j in range(columns):
                # print grid elements with no newline
                print maze[rows - (i + 1)][j], "|",
            # A new line after each line of the grid
            print 
        # A line after the grid
        print

    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        walls = api.walls(state)
        corners = api.corners(state)
        pacman = api.whereAmI(state)

        reward = -1
        discount = 0.95
        food_utility = 7
        ghost_utility = -500
        
        actions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]

        size = corners[len(corners) - 1]
        columns = size[0] + 1 # x coordinate 
        rows = size[1] + 1 # y coordinate
        
        # Adding the positions of the maze to a list.
        states = []
        for i in range(columns):
            for j in range(rows):
                if (i, j) not in walls:
                    states.append((i, j))

        maze = self.map(state, food_utility, ghost_utility) # Initialize the maze
        maze = self.value_iteration(maze, reward, discount) # Perform value iteration on the maze

        #print "Pacman", pacman

        self.print_maze(maze)
    
        near = self.nearby(pacman, maze)
        max_utility = (float("-inf"), Directions.STOP)
        for key in near:
            if near[key] >= max_utility[0]:
                max_utility = (near[key], key)

        print "Max utility", max_utility
        # Random choice between the legal options.
        return api.makeMove(max_utility[1], legal)
