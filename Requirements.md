# CMPT 371 Summer 2025 – Project

## Overview

In this project, your group will build an **online multiplayer game**. The game itself is up to you, though a suggested game called **Deny and Conquer** is described below.

---

## Group Signup

- This project is to be done in **groups of 4 students**.
- Go to **Canvas → People → Project Group** and sign up to any group that has room left for you and, if applicable, your teammates.
- On **July 14 afternoon**, the professor will assign to random groups with available space whoever hasn’t signed up yet.

---

## Game Requirements

- The game **shall be a client-server program**. Each player is a client connecting to the server from a remote machine/device.
- The **server can be started by anyone**. All players connect to that server as clients.
- There must be at least **one shared object in the game** which requires “locking” of that object for concurrency; i.e., **only one player at a time can use that object**. In the Deny and Conquer game, each white square is a shared object.

---

## Technical Rules

- You can use **any programming language** that you like.
- For the **frontend**, you can use any existing graphics or GUI library or framework. Make your life easy for the frontend as much as possible. Don’t overdo the GUI. A simple and functional GUI is enough.
- For the **backend (client and server system)**, you **cannot use any existing gaming, client-server, messaging, remote calling, or other middleware or frameworks**.  
  **Everything must be written from scratch.**  
  You **must use sockets programming and send application-layer messages directly**.

---

## Deliverables

### a. Project Report

- **Description of the game and your design**, including your application-layer messaging scheme.  
  Please show and explain the code snippets where you are:
  - **Opening sockets**
  - **Handling the shared object**

### b. List of Group Members

- Include a list of group members and their **individual contribution percentage**.  
  Each group member is expected to contribute equally; e.g., 25% for a 4-person group, or 20% for a 5-person group.

### c. Source Code

- **Commented source code** that can be checked out, compiled, and run.
- The code should be on **Github or another repository** and include a **README** file that provides instructions on how to compile and run the code.
- Make the repository **public** or provide a link in your report that gives access to the TA.

### d. Video Demo

- **Video of a working demo.**
- Upload the video somewhere and put its link in the final report.
- The video **must be 1 to 2 minutes**, show at least **3 players playing the game** and the shared object in action.

---

## Marking Scheme


Group project mark = 30% working demo (as seen in the video) + 70% report

Individual mark = group project mark × individual contribution × size of group


- **Individual mark** is the mark that is given to an individual student as the final mark for the project.
- **Individual contribution** is an individual student’s percentage contribution, capped at 100%.
- **Size of group**: number of group members.

---

## Deny and Conquer

**The game board is divided into squares of equal size. The number of squares shall be 8×8.**  
The game is played by multiple players, each having a pen of different colour. The thickness of the pen is the same for all players.

### Objective

The objective is to **deny your opponents filling the most number of squares, by taking over as many squares as you can**. To take over a square:

1. The square must be **white**.
2. Put your pen down (click the mouse button) in that square and **scribble, without lifting the pen** (hold the mouse button down), until in your judgement at least **50% of the area of the square is coloured**.
3. You can then lift your pen (release the mouse button).
4. When you lift your pen, the game engine will:
   - Turn the colour of that square to your colour, **if at least 50% of the surface is coloured**.
   - Otherwise, the square will turn **completely white** and another player can try taking over it.

At the end of the game (**when all squares have been taken over**), whoever has the most number of squares **wins** the game. Tie is also possible.

---

### Game Mechanics

- While a player is **scribbling in a square**, that square is **no longer available to other players**.
- If those other players click in that square, **they should not be able to draw anything in it**.

---



