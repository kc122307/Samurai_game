# 🗡️ Samurai Runner: The Unbeatable Path
*A complete Samurai Endless Runner Game built in Python + Pygame with Dragons, Power-ups, Particles, Parallax Worlds, and Day/Night Cycles.*

---

<div align="center">

### 🎮 Gameplay Demo  
▶️ https://www.youtube.com/watch?v=11gxu2jxQ6s  

[![Gameplay Demo](https://img.youtube.com/vi/11gxu2jxQ6s/maxresdefault.jpg)](https://www.youtube.com/watch?v=11gxu2jxQ6s)

---

## 🔥 Built With  
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.5-green.svg)
![NumPy](https://img.shields.io/badge/NumPy-Audio-orange.svg)
![License](https://img.shields.io/badge/License-MIT-success.svg)

</div>

---

# 📌 Overview
**Samurai Runner: The Unbeatable Path** is a fast-paced, action-packed endless runner where you control a Samurai sprinting across a mystical world filled with dragons, obstacles, magical power-ups, and dynamic environmental transitions.

Everything—from movement physics, obstacle spawning, audio synthesis, particle decay, animated dragons, and collision detection—is coded manually in **Python + Pygame**.

---

# 🎮 Game Features

## 🐉 Obstacles & Enemies
- Rocks  
- Barrels  
- Bamboo  
- Boulders  
- Flying Dragons (Red / Green / Black)  
- Low / Mid / High altitude patterns  
- Pixel-perfect collision using masks  

## 🌗 Dynamic Day/Night Cycle
- Smooth transitions  
- Petals during day  
- Sparkles at night  
- Sun + Moon movement  
- Ambient lighting  

## 💠 Power-ups
### 🔵 Blue Dash  
- Temporary invincibility  
- Faster movement  
- Blue aura trail  

### 🟡 Yellow Tornado  
- Automatically destroys the next obstacle  
- Wood debris explosion  

## ✨ Particle System
- Dust clouds  
- Petals  
- Sparks  
- Magic particles  
- Wood debris  
- Alpha-based fade decay  

## 🔊 Audio Engine (NumPy)
- Jump sound  
- Double jump sound  
- Tornado effect  
- Score milestone chime  
- Hit/death noise burst  

All audio is generated **procedurally**, not pre-recorded.

---

# 🖼️ Screenshots
(Add your own images)

```
screenshots/
 ├── gameplay1.png
 ├── gameplay2.png
 ├── dragons.png
 └── nightmode.png
```

Example embed:
```markdown
![Gameplay Screenshot](screenshots/gameplay1.png)
```

---

# ⚙️ How the Game Works

## 🎯 Core Mechanics
- Continuous side-scrolling  
- Random obstacle generation  
- Dragon flight path logic  
- Player physics & animation  
- Power-up timers  
- Mask-based collision  

## 🧠 Difficulty Scaling
The game becomes harder every second:
- Faster speed  
- Shorter obstacle spacing  
- More dragons

---

# 🚀 Installation & Running

## 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/samurai-runner
cd samurai-runner
```

## 2️⃣ Install Requirements
```bash
pip install pygame numpy
```

## 3️⃣ Run the Game
```bash
python app1.py
```

---

# 🎮 Controls

| Action | Key |
|--------|-----|
| Jump | Space / ↑ |
| Double Jump | Space Again |
| Duck | ↓ |
| Toggle Day/Night | T |
| Spawn Dragon (Debug) | G |
| Show Hitboxes | H |

---

# 📂 Project Structure

```
samurai-runner/
│── app1.py                     # Main game engine
│── highscore.txt               # Score saving
│── images/
│    ├── obstacles/             # Custom obstacles
│    ├── samurai/               # Samurai animations
│    ├── dragon.gif             # Dragon animation (auto-split)
│    └── backgrounds/
│── screenshots/                # (Optional for README)
│── README.md
│── requirements.txt
```

---

# 🧠 Technical Architecture

## 🟩 AssetLoader
- Loads + scales images  
- GIF → frame extraction  
- Crops transparent borders  
- Auto-detects custom obstacles  

## 🟥 Samurai Class
- Jump physics  
- Ducking  
- Double jump  
- Power-up effects  
- Animation cycling  

## 🟦 Obstacle System
- Procedural spawning  
- Multiple types  
- Mask-based collision  

## 🟪 Environment Class
- Parallax scrolling  
- Day/night transitions  
- Sun + Moon movement  
- Lanterns, clouds, pagodas  

## 🟨 Particle Engine
- Dust  
- Debris  
- Sparks  
- Petals  

## 🟧 Audio Engine
- NumPy waveform synthesis  
- Real-time sound generation  

---

# 🧩 Custom Asset Support

### ✔ Add custom obstacles  
Place images inside:
```
images/obstacles/
```

### ✔ Add custom dragons  
Place animated GIFs inside:
```
images/
```

### ✔ Add new Samurai skins  
Place sprite folders inside:
```
images/samurai/
```

The engine will auto-detect them.

---

# ⚡ Optimization Notes
- Cached images & masks  
- Preloaded dragon GIF frames  
- Bounding box pre-check before mask collision  
- Efficient particle cleanup  
- GPU-friendly sprite scaling  
- Optimized spawn logic  

---

# 🛠 Troubleshooting

### ❗ Game does not launch?
Update pygame:
```bash
pip install pygame --upgrade
```

### ❗ NumPy audio warning?
Game still runs perfectly.

### ❗ Performance issues?
Try:
- Closing background apps  
- Lower resolution assets  
- Running on Python 3.10+  

---

# 🧭 Future Roadmap
- [ ] Boss battles  
- [ ] Weather FX (rain, snow, thunder)  
- [ ] Unlockable characters  
- [ ] XP + Shop system  
- [ ] Online leaderboard  
- [ ] Multiplayer mode  
- [ ] Mobile version (Kivy/React Native)  

---

# 🤝 Contributing
Pull requests and feature additions are welcome.  
Feel free to improve sprites, add animations, or optimize code.

---

# 📄 License
This project is licensed under the **MIT License** — free for personal or commercial use with credit.

---

# 🙏 Credits
- Game Development: **You**  
- Sprites & Assets: User-provided  
- Dragon GIF support: Auto-extracted  
- All audio generated using NumPy  

---

# 🔖 GitHub Hashtags (SEO)
```
#Python #Pygame #GameDevelopment #OpenSource #EndlessRunner
#Samurai #Dragons #2DGame #PythonDeveloper #IndieGame
#Particles #DayNightCycle #PygameProject #Coding #Developer
```
