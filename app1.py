import pygame
import random
import sys
import math
import os
import time

# Try importing numpy for sound synthesis
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False
    print("WARNING: NumPy not found. Audio will be disabled.")

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
class Config:
    # Screen
    SCREEN_WIDTH = 960
    SCREEN_HEIGHT = 540
    FPS = 60
    TITLE = "Samurai Runner: The Unbeatable Path"

    # Physics
    GRAVITY = 0.65
    JUMP_FORCE = -12.5
    DOUBLE_JUMP_FORCE = -10.0
    GROUND_Y = 420
    
    # Speed
    START_SPEED = 6.0
    MAX_SPEED = 16.0
    SPEED_INCREMENT = 0.0015

    # Gameplay
    SCORE_PER_FRAME = 0.2
    NIGHT_CYCLE_FRAMES = 1200 # Frames until day/night switch

    # Colors
    COLORS = {
        'day_sky': (135, 206, 235),      # Sky Blue
        'night_sky': (25, 25, 60),       # Deep Navy
        'ground': (101, 67, 33),         # Earth Brown
        'grass': (50, 200, 50),
        'text': (255, 255, 255),
        'text_shadow': (0, 0, 0),
        'ui_bg': (0, 0, 0, 150)          # Semi-transparent black
    }

# ==============================================================================
# 2. AUDIO ENGINE (Procedural Sound Synthesis)
# ==============================================================================
class AudioManager:
    """
    Generates retro game sounds using NumPy so no external .wav files are needed.
    """
    def __init__(self):
        self.enabled = HAS_NUMPY
        self.sounds = {}
        if self.enabled:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.generate_sounds()

    def generate_sounds(self):
        """Pre-calculates sound waves"""
        self.sounds['jump'] = self._make_tone(440, 0.1, shape='square', slide=100)
        self.sounds['double_jump'] = self._make_tone(660, 0.1, shape='sine', slide=200)
        self.sounds['slash'] = self._make_noise(0.15, fade_out=True)
        self.sounds['hit'] = self._make_noise(0.3, pitch_drop=True)
        # Use a simple pleasant tone for powerup to avoid None
        self.sounds['powerup'] = self._make_tone(554, 0.12, shape='sine', slide=120)
        self.sounds['score'] = self._make_tone(880, 0.05, shape='sine')

    def play(self, name):
        snd = self.sounds.get(name)
        if self.enabled and snd is not None:
            try:
                snd.play()
            except Exception:
                pass

    def _make_tone(self, freq, duration, vol=0.5, shape='sine', slide=0):
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        # Frequency slide logic
        if slide != 0:
            freq = np.linspace(freq, freq + slide, n_samples)
        
        if shape == 'sine':
            waveform = np.sin(2 * np.pi * freq * t)
        elif shape == 'square':
            waveform = np.sign(np.sin(2 * np.pi * freq * t))
        
        # Envelope (Fade out)
        envelope = np.linspace(1, 0, n_samples)
        
        # Stereo duplication and int16 conversion
        audio_data = (waveform * envelope * vol * 32767).astype(np.int16)
        audio_data = np.repeat(audio_data[:, np.newaxis], 2, axis=1)
        return pygame.sndarray.make_sound(audio_data)

    def _make_noise(self, duration, vol=0.5, fade_out=True, pitch_drop=False):
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        waveform = np.random.uniform(-1, 1, n_samples)
        
        if fade_out:
            envelope = np.linspace(1, 0, n_samples)
            waveform *= envelope
            
        audio_data = (waveform * vol * 32767).astype(np.int16)
        audio_data = np.repeat(audio_data[:, np.newaxis], 2, axis=1)
        return pygame.sndarray.make_sound(audio_data)

    def _make_sequence(self, freqs, step_dur):
        # Combine multiple tones
        pass # Simplified for brevity, usually concatenates arrays

# ==============================================================================
# 3. ASSET LOADER (Sprite Cutting)
# ==============================================================================
class AssetLoader:
    def __init__(self, images_dir='images'):
        self.sheet = None
        self.sprites = {}
        self.images_dir = images_dir
        # We don't rely on a sprite sheet anymore; load individual files if they exist.

    def _load_image_file(self, filename, scale=1.0):
        path = os.path.join(self.images_dir, filename)
        try:
            img = pygame.image.load(path).convert_alpha()
            if scale != 1.0:
                w, h = img.get_width(), img.get_height()
                img = pygame.transform.scale(img, (int(w*scale), int(h*scale)))
            return img
        except Exception:
            return None

    def _make_surface(self, w, h, draw_fn=None):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        if draw_fn:
            draw_fn(surf)
        return surf

    def load_all(self):
        # Samurai frames from images/ folder
        left = self._load_image_file('Running_leftLeg.png')
        right = self._load_image_file('RIght_leg.png') or self._load_image_file('Right_leg.png')
        # If only one run frame available, synthesize the other by flipping
        if left is not None and right is None:
            right = pygame.transform.flip(left, True, False)
        if right is not None and left is None:
            left = pygame.transform.flip(right, True, False)
        still = self._load_image_file('Still_samurai.png')
        jump = self._load_image_file('Jump_samrai.png')
        duck = self._load_image_file('Down_samrai.png')

        # Fallback simple silhouettes if any missing
        def placeholder_samurai(w=100, h=120):
            return self._make_surface(w, h, lambda s: pygame.draw.rect(s, (50,50,50), (20, 20, w-40, h-40), border_radius=10))

        self.sprites['run'] = [left or placeholder_samurai(), right or (left and pygame.transform.flip(left, True, False)) or placeholder_samurai()]
        self.sprites['jump'] = jump or (still or placeholder_samurai())
        self.sprites['duck'] = duck or self._make_surface(120, 80, lambda s: pygame.draw.rect(s, (50,50,50), (10,20,100,50), border_radius=8))

        # FX
        self.sprites['tornado'] = self._make_surface(120, 120, lambda s: [
            pygame.draw.arc(s, (200,200,255), (0,0,120,120), 0.5, 2.5, 6),
            pygame.draw.arc(s, (160,160,220), (10,10,100,100), 0.6, 2.6, 5)
        ])
        # Blue dash flame
        self.sprites['dash_flame'] = self._make_surface(80, 80, lambda s: [
            pygame.draw.circle(s, (100,180,255,180), (40,40), 28),
            pygame.draw.circle(s, (150,220,255,160), (40,40), 18)
        ])
        # Ticket powerups
        def ticket(color):
            return self._make_surface(40, 30, lambda s: [
                pygame.draw.rect(s, color, (0,0,40,30), border_radius=6),
                pygame.draw.rect(s, (255,255,255,60), (4,4,32,22), 2, border_radius=4)
            ])
        self.sprites['ticket_blue'] = ticket((80,160,255))
        self.sprites['ticket_yellow'] = ticket((255,215,64))
        # Try to override with provided ticket images
        try:
            for fname in os.listdir(self.images_dir):
                low = fname.lower()
                if 'ticket' in low and any(ext in low for ext in ['.png', '.jpg', '.jpeg']):
                    img = self._load_image_file(fname)
                    if img is None:
                        continue
                    if 'blue' in low:
                        self.sprites['ticket_blue'] = img
                    elif 'yellow' in low:
                        self.sprites['ticket_yellow'] = img
        except Exception:
            pass

        # Obstacles (procedural placeholders)
        self.sprites['rock'] = self._make_surface(40, 40, lambda s: pygame.draw.circle(s, (130,130,130), (20,20), 18))
        self.sprites['barrel'] = self._make_surface(70, 70, lambda s: [
            pygame.draw.rect(s, (139,69,19), (5,5,60,60), border_radius=6),
            pygame.draw.line(s, (90,50,10), (5,20), (65,20), 4),
            pygame.draw.line(s, (90,50,10), (5,45), (65,45), 4)
        ])
        self.sprites['bamboo'] = self._make_surface(60, 140, lambda s: [
            pygame.draw.rect(s, (40,160,60), (25,0,10,140)),
            pygame.draw.line(s, (80,200,100), (25,20), (35,20), 3),
            pygame.draw.line(s, (80,200,100), (25,60), (35,60), 3),
            pygame.draw.line(s, (80,200,100), (25,100), (35,100), 3)
        ])
        self.sprites['boulder'] = self._make_surface(120, 120, lambda s: pygame.draw.circle(s, (110,110,110), (60,60), 56))

        # Attempt to override with provided obstacle images if present
        rock_img = self._load_image_file('rock.png')
        if rock_img: self.sprites['rock'] = rock_img
        drum_img = self._load_image_file('drum.png') or self._load_image_file('barrel.png')
        if drum_img: self.sprites['barrel'] = drum_img
        bamboo_img = self._load_image_file('bamboo.png')
        if bamboo_img: self.sprites['bamboo'] = bamboo_img
        # Default: mark boulder image unavailable until set
        self.sprites['boulder_image_available'] = False
        boulder_img = self._load_image_file('boulder.png')
        if boulder_img:
            self.sprites['boulder'] = boulder_img
            self.sprites['boulder_image_available'] = True

        # Multiple drum variants: scan folder for any names containing 'drum', 'barrel', or 'dum'
        drum_variants = []
        try:
            for fname in os.listdir(self.images_dir):
                low = fname.lower()
                if ('drum' in low) or ('barrel' in low) or ('dum' in low):
                    img = self._load_image_file(fname)
                    if img:
                        drum_variants.append(img)
        except Exception:
            pass
        if drum_variants:
            self.sprites['barrel_variants'] = drum_variants
            # Also set default barrel to first variant
            self.sprites['barrel'] = drum_variants[0]

        # Rock variants: scan for names containing 'rock' or 'stone'
        rock_variants = []
        try:
            for fname in os.listdir(self.images_dir):
                low = fname.lower()
                if ('rock' in low) or ('stone' in low):
                    img = self._load_image_file(fname)
                    if img:
                        rock_variants.append(img)
        except Exception:
            pass
        if rock_variants:
            self.sprites['rock_variants'] = rock_variants
            self.sprites['rock'] = rock_variants[0]
            # If no dedicated boulder image, reuse a rock variant for boulder to avoid procedural round
            if not self.sprites.get('boulder_image_available', False):
                self.sprites['boulder'] = rock_variants[0]
                self.sprites['boulder_image_available'] = True

        # Bamboo variants: scan for names containing 'bamboo'
        bamboo_variants = []
        try:
            for fname in os.listdir(self.images_dir):
                low = fname.lower()
                if 'bamboo' in low:
                    img = self._load_image_file(fname)
                    if img:
                        bamboo_variants.append(img)
        except Exception:
            pass
        if bamboo_variants:
            self.sprites['bamboo_variants'] = bamboo_variants
            self.sprites['bamboo'] = bamboo_variants[0]

        # Backgrounds: scan for day/night images
        day_bg = None
        night_bg = None
        try:
            for fname in os.listdir(self.images_dir):
                low = fname.lower()
                if ('day' in low) and any(ext in low for ext in ['.png', '.jpg', '.jpeg']):
                    day_bg = self._load_image_file(fname)
                if ('night' in low) and any(ext in low for ext in ['.png', '.jpg', '.jpeg']):
                    night_bg = self._load_image_file(fname)
        except Exception:
            pass
        if day_bg: self.sprites['bg_day'] = day_bg
        if night_bg: self.sprites['bg_night'] = night_bg

        # Generic obstacle variants: names containing 'obstacle' or common typos
        generic_variants = []
        try:
            for fname in os.listdir(self.images_dir):
                low = fname.lower()
                if any(key in low for key in ['obstacle', 'obastcle', 'obactcle', 'obatcle']):
                    if any(ext in low for ext in ['.png', '.jpg', '.jpeg']):
                        img = self._load_image_file(fname)
                        if img:
                            generic_variants.append(img)
        except Exception:
            pass
        if generic_variants:
            self.sprites['obstacle_variants'] = generic_variants

        # Dragons: use Dragon.gif if present, otherwise procedural frames
        def crop_visible(surf):
            # Use Surface.get_bounding_rect to compute union of non-transparent pixels
            r = surf.get_bounding_rect(min_alpha=1)
            if r.width == 0 or r.height == 0:
                return surf
            cropped = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            cropped.blit(surf, (0,0), r)
            return cropped
        def revive_alpha_from_rgb(surf, threshold=1):
            # Rebuild alpha channel from RGB brightness so transparent GIFs become visible
            import numpy as _np
            w, h = surf.get_width(), surf.get_height()
            out = pygame.Surface((w, h), pygame.SRCALPHA)
            rgb = pygame.surfarray.array3d(surf)  # (w,h,3)
            # Copy RGB
            pygame.surfarray.blit_array(out, rgb)
            # Compute brightness -> alpha; set fully opaque where above threshold
            gray = (0.299*rgb[:, :, 0] + 0.587*rgb[:, :, 1] + 0.114*rgb[:, :, 2])
            alpha = _np.where(gray > threshold, 255, 0).astype(_np.uint8)
            aview = pygame.surfarray.pixels_alpha(out)
            aview[:, :] = alpha
            del aview
            return out

        def tint_frames(frames, color):
            out = []
            for f in frames:
                s = f.copy()
                tint = pygame.Surface(s.get_size(), pygame.SRCALPHA)
                tint.fill(color)
                s.blit(tint, (0,0), special_flags=pygame.BLEND_RGB_MULT)
                out.append(s)
            return out

        dragon_gif = None
        gif_frames = None
        try:
            for fname in os.listdir(self.images_dir):
                low = fname.lower()
                if 'dragon' in low and low.endswith('.gif'):
                    path = os.path.join(self.images_dir, fname)
                    try:
                        from PIL import Image
                        im = Image.open(path)
                        frames = []
                        n = getattr(im, 'n_frames', 1)
                        for i in range(max(1, n)):
                            im.seek(i)
                            fr = im.convert('RGBA')
                            w, h = fr.size
                            surf = pygame.image.fromstring(fr.tobytes(), (w, h), 'RGBA')
                            frames.append(surf)
                        gif_frames = frames
                    except Exception:
                        dragon_gif = self._load_image_file(fname)
                    break
        except Exception:
            pass

        if gif_frames:
            proc = []
            for f in gif_frames:
                try:
                    f = revive_alpha_from_rgb(f)
                except Exception:
                    pass
                c = crop_visible(f)
                proc.append(c)
            if len(proc) == 1:
                f1 = proc[0]
                w, h = f1.get_size()
                f2s = pygame.transform.smoothscale(f1, (w, max(1, int(h*0.92))))
                canvas = pygame.Surface((w, h), pygame.SRCALPHA)
                canvas.blit(f2s, (0, h - f2s.get_height()))
                proc.append(crop_visible(canvas))
            self.sprites['dragon'] = proc
            try:
                m0 = pygame.mask.from_surface(proc[0])
                print(f"Dragon.gif frames={len(proc)} pixels0={m0.count()} size0={proc[0].get_size()}")
            except Exception:
                pass
        elif dragon_gif is not None:
            f1 = dragon_gif.convert_alpha() if hasattr(dragon_gif, 'convert_alpha') else dragon_gif
            w, h = f1.get_size()
            f2 = pygame.transform.smoothscale(f1, (w, max(1, int(h*0.9))))
            canvas2 = pygame.Surface((w, h), pygame.SRCALPHA)
            canvas2.blit(f2, (0, h - f2.get_height()))
            try:
                f1 = revive_alpha_from_rgb(f1)
                canvas2 = revive_alpha_from_rgb(canvas2)
            except Exception:
                pass
            c1 = crop_visible(f1)
            c2 = crop_visible(canvas2)
            self.sprites['dragon'] = [c1, c2]
        else:
            base1 = self._make_surface(110, 90, lambda s: pygame.draw.polygon(s, (180,180,180), [(10,70),(60,20),(100,50),(60,60)]))
            base2 = self._make_surface(110, 90, lambda s: pygame.draw.polygon(s, (180,180,180), [(10,50),(60,10),(100,40),(60,70)]))
            self.sprites['dragon'] = [base1, base2]

        # Color variants (used for speed/height variation)
        self.sprites['dragon_red'] = tint_frames(self.sprites['dragon'], (255, 120, 120))
        self.sprites['dragon_green'] = tint_frames(self.sprites['dragon'], (120, 255, 120))
        self.sprites['dragon_black'] = tint_frames(self.sprites['dragon'], (90, 90, 90))
        self.sprites['dragon_user_frames'] = bool(gif_frames or dragon_gif)
        if self.sprites['dragon_user_frames']:
            self.sprites['dragon_red'] = list(self.sprites['dragon'])
            self.sprites['dragon_green'] = list(self.sprites['dragon'])
            self.sprites['dragon_black'] = list(self.sprites['dragon'])

        # Obstacles-in-folder mode: scan images/obstacles or images/obatcles
        folder_paths = []
        p1 = os.path.join(self.images_dir, 'obstacles')
        p2 = os.path.join(self.images_dir, 'obatcles')  # handle common typo
        if os.path.isdir(p1):
            folder_paths.append(p1)
        if os.path.isdir(p2):
            folder_paths.append(p2)

        folder_obstacles = []
        folder_dragons = []
        try:
            for base in folder_paths:
                for fname in os.listdir(base):
                    low = fname.lower()
                    if not any(low.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                        continue
                    full = os.path.join(base, fname)
                    # Special-case dragon gifs (or any file with 'dragon') as animated flying
                    if 'dragon' in low and low.endswith('.gif'):
                        gif_img = pygame.image.load(full).convert_alpha()
                        w, h = gif_img.get_size()
                        f2 = pygame.transform.smoothscale(gif_img, (w, max(1, int(h*0.9))))
                        canvas2 = pygame.Surface((w, h), pygame.SRCALPHA)
                        canvas2.blit(f2, (0, h - f2.get_height()))
                        # Rebuild alpha in case GIF lost it, then crop
                        try:
                            gif_img = revive_alpha_from_rgb(gif_img)
                            canvas2 = revive_alpha_from_rgb(canvas2)
                        except Exception:
                            pass
                        c1 = crop_visible(gif_img)
                        c2 = crop_visible(canvas2)
                        folder_dragons.append({'name': fname, 'frames': [c1, c2]})
                        # Diagnostics: print visible pixel count for folder dragon
                        try:
                            m1 = pygame.mask.from_surface(c1); m2 = pygame.mask.from_surface(c2)
                            print(f"Dragon.gif loaded (folder): {fname} Visible pixels: f1={m1.count()} f2={m2.count()} size1={c1.get_size()} size2={c2.get_size()}")
                        except Exception:
                            pass
                    else:
                        img = pygame.image.load(full).convert_alpha()
                        folder_obstacles.append({'name': fname, 'img': img})
        except Exception:
            pass

        if folder_obstacles:
            self.sprites['folder_obstacles'] = folder_obstacles
        if folder_dragons:
            self.sprites['folder_dragons'] = folder_dragons
        # Debug prints to confirm folder mode
        if folder_paths:
            try:
                total_o = len(folder_obstacles)
                total_d = len(folder_dragons)
                print(f"Folder mode scan: paths={folder_paths} | obstacles={total_o} | dragons={total_d}")
            except Exception:
                pass

        # STRICT MODE: if user provided any folder obstacles, or generic obstacle images in images/, or a user dragon gif,
        # then spawn ONLY from those, no procedural placeholders.
        strict_ground = []
        # 1) From folders
        if 'folder_obstacles' in self.sprites:
            strict_ground.extend(self.sprites['folder_obstacles'])
        # 2) From images root generic obstacle* set gathered earlier (if any)
        if 'obstacle_variants' in self.sprites:
            # Wrap to uniform dict form: {'img': img}
            for img in self.sprites['obstacle_variants']:
                strict_ground.append({'img': img})

        strict_dragons = []
        # 1) From folders
        if 'folder_dragons' in self.sprites:
            strict_dragons.extend(self.sprites['folder_dragons'])
        # 2) From images root Dragon.gif (only if actually present)
        if self.sprites.get('dragon_user_frames', False):
            strict_dragons.append({'frames': self.sprites['dragon']})

        self.sprites['strict_mode'] = (len(strict_ground) > 0) or (len(strict_dragons) > 0)
        if self.sprites['strict_mode']:
            self.sprites['strict_ground'] = strict_ground
            self.sprites['strict_dragons'] = strict_dragons
            try:
                print(f"Strict image obstacle mode: ground={len(strict_ground)} | dragons={len(strict_dragons)}")
            except Exception:
                pass

        # Items
        self.sprites['talisman'] = self._make_surface(30, 40, lambda s: [
            pygame.draw.rect(s, (255, 235, 120), (5,5,20,30), border_radius=4),
            pygame.draw.line(s, (220, 160, 40), (10,12), (20,28), 3)
        ])
        self.sprites['scroll'] = self._make_surface(40, 40, lambda s: pygame.draw.rect(s, (220,220,220), (5,8,30,24), border_radius=4))

        # Env placeholders
        self.sprites['pagoda'] = self._make_surface(150, 120, lambda s: [
            pygame.draw.rect(s, (60,60,80), (50,40,50,70)),
            pygame.draw.polygon(s, (80,80,110), [(35,40),(75,10),(115,40)])
        ])
        self.sprites['lantern'] = self._make_surface(40, 60, lambda s: [
            pygame.draw.ellipse(s, (255,140,0), (5,10,30,40)),
            pygame.draw.circle(s, (255,220,120), (20,30), 6)
        ])

# ==============================================================================
# 4. PARTICLE SYSTEM
# ==============================================================================
class Particle:
    def __init__(self, x, y, p_type):
        self.x = x
        self.y = y
        self.type = p_type
        self.life = 1.0 # 0.0 to 1.0
        self.decay = random.uniform(0.02, 0.05)
        
        if p_type == 'petal': # Cherry blossom
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(0.5, 1.5)
            self.color = (255, 183, 197)
            self.size = random.randint(3, 5)
        elif p_type == 'debris': # Broken wood
            self.vx = random.uniform(-5, 5)
            self.vy = random.uniform(-6, -2)
            self.color = (139, 69, 19)
            self.size = random.randint(4, 7)
        elif p_type == 'sparkle': # Powerup
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(-2, -0.5)
            self.color = (255, 255, 0)
            self.size = random.randint(2, 4)
        elif p_type == 'dust': # Running dust
            self.vx = random.uniform(-2, -0.5)
            self.vy = random.uniform(-0.5, 0)
            self.color = (200, 200, 200)
            self.size = random.randint(3, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        
        if self.type == 'debris':
            self.vy += 0.4 # Gravity for debris

    def draw(self, surf):
        if self.life > 0:
            alpha = int(self.life * 255)
            # Create a temporary surface for transparency
            s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
            surf.blit(s, (self.x - self.size, self.y - self.size))

# ==============================================================================
# 5. GAME ENTITIES
# ==============================================================================
class Samurai:
    def __init__(self, assets):
        self.assets = assets
        self.reset()
        
    def reset(self):
        self.x = 100
        self.y = Config.GROUND_Y
        self.vel_y = 0
        # Smaller on-screen size
        self.width = 48
        self.height = 72
        
        # State Flags
        self.is_jumping = False
        self.can_double_jump = False
        self.is_ducking = False
        self.run_frame = 0
        self.anim_timer = 0
        
        # Powerups
        self.dash_timer = 0      # frames of invulnerability
        self.tornado_ready = False   # single-use destroy next obstacle
        self.double_jump_item = False 
        self.jump_anim_t = 0
        

    def jump(self, audio):
        if self.is_ducking:
            self.is_ducking = False
            self.height = 90
            self.y = Config.GROUND_Y - 90

        if not self.is_jumping:
            self.vel_y = Config.JUMP_FORCE
            self.is_jumping = True
            self.jump_anim_t = 0
            audio.play('jump')
            # Create dust
            return 'dust'
        elif self.double_jump_item and self.can_double_jump:
            self.vel_y = Config.DOUBLE_JUMP_FORCE
            self.can_double_jump = False
            self.double_jump_item = False # Consumable or Permanent? Let's make it consumable for balance
            audio.play('double_jump')
            return 'sparkle'
        return None

    def duck(self, is_ducking):
        if not self.is_jumping:
            self.is_ducking = is_ducking
            if is_ducking:
                self.height = 50
                self.y = Config.GROUND_Y - 50
            else:
                self.height = 90
                self.y = Config.GROUND_Y - 90

    def activate_powerup(self, p_type, audio):
        audio.play('powerup')
        if p_type == 'BLUE':
            self.dash_timer = 300 # 5 seconds at 60 FPS
        elif p_type == 'YELLOW':
            self.tornado_ready = True # destroy next obstacle

    def update(self):
        # Apply Gravity
        self.vel_y += Config.GRAVITY
        self.y += self.vel_y

        # Ground Collision
        ground_level = Config.GROUND_Y - self.height
        if self.y >= ground_level:
            self.y = ground_level
            self.vel_y = 0
            self.is_jumping = False
            self.can_double_jump = True
            

        # Tick Timers
        if self.dash_timer > 0: self.dash_timer -= 1
        if self.is_jumping: self.jump_anim_t += 1

        # Animate
        self.anim_timer += 1
        if self.anim_timer >= 5:
            self.run_frame = (self.run_frame + 1) % 2
            self.anim_timer = 0

    def draw(self, surf):
        # Draw Effects (Behind character)
        if self.dash_timer > 0:
            # Blue dash effect
            flame = self.assets.get('dash_flame', None)
            if flame:
                # Scale dash flame roughly to character size
                f = pygame.transform.smoothscale(flame, (int(self.width*1.6), int(self.height*1.2)))
                surf.blit(f, (self.x - int(self.width*0.6), self.y - int(self.height*0.15)))
        
        if self.tornado_ready:
            # Show tornado ready effect subtly
            spin_angle = (pygame.time.get_ticks() // 10) % 360
            orig_img = self.assets['tornado']
            rot_img = pygame.transform.rotate(orig_img, spin_angle)
            rect = rot_img.get_rect(center=(self.x + 30, self.y + 45))
            surf.blit(rot_img, rect)

        # Draw Sprite (scaled to width/height)
        img = None
        if self.is_ducking and not self.is_jumping:
            base = self.assets['duck']
            img = pygame.transform.smoothscale(base, (self.width, self.height))
        elif self.is_jumping:
            base = self.assets['jump']
            scaled = pygame.transform.smoothscale(base, (self.width, self.height))
            # No rotation for jump; show provided jump sprite as-is
            surf.blit(scaled, (self.x, self.y))
            if self.double_jump_item:
                surf.blit(self.assets['talisman'], (self.x + 10, self.y - 40))
            return
        else:
            base = self.assets['run'][self.run_frame]
            img = pygame.transform.smoothscale(base, (self.width, self.height))
        
        # Align top-left so feet meet ground
        surf.blit(img, (self.x, self.y))

        # Visual indicator for double jump
        if self.double_jump_item:
            surf.blit(self.assets['talisman'], (self.x + 10, self.y - 40))

    def get_hitbox(self):
        # Tighter player hitbox to avoid early collisions
        return pygame.Rect(self.x + 14, self.y + 12, self.width - 28, self.height - 24)

    def get_surface_and_rect(self):
        # Returns current scaled surface and its rect at (x, y)
        if self.is_ducking and not self.is_jumping:
            base = self.assets['duck']
        elif self.is_jumping:
            base = self.assets['jump']
        else:
            base = self.assets['run'][self.run_frame]
        surf = pygame.transform.smoothscale(base, (self.width, self.height))
        return surf, pygame.Rect(self.x, self.y, self.width, self.height)


class Obstacle:
    def __init__(self, x, o_type, assets, data=None):
        self.x = x
        self.type = o_type
        self.assets = assets
        self.passed = False
        self.rotation = 0
        
        if o_type == 'rock':
            if 'obstacle_variants' in assets and assets['obstacle_variants']:
                self.img = random.choice(assets['obstacle_variants'])
            elif 'rock_variants' in assets and assets['rock_variants']:
                self.img = random.choice(assets['rock_variants'])
            else:
                self.img = assets['rock']
            self.rect = pygame.Rect(x, Config.GROUND_Y - 36, 36, 36)
        elif o_type == 'barrel':
            # Use random drum variant if available
            if 'obstacle_variants' in assets and assets['obstacle_variants']:
                self.img = random.choice(assets['obstacle_variants'])
            elif 'barrel_variants' in assets and assets['barrel_variants']:
                self.img = random.choice(assets['barrel_variants'])
            else:
                self.img = assets['barrel']
            self.rect = pygame.Rect(x, Config.GROUND_Y - 56, 56, 56)
        elif o_type == 'bamboo':
            if 'obstacle_variants' in assets and assets['obstacle_variants']:
                self.img = random.choice(assets['obstacle_variants'])
            elif 'bamboo_variants' in assets and assets['bamboo_variants']:
                self.img = random.choice(assets['bamboo_variants'])
            else:
                self.img = assets['bamboo']
            self.rect = pygame.Rect(x + 15, Config.GROUND_Y - 110, 26, 110) # Slightly shorter, thinner
        elif o_type == 'boulder':
            if 'obstacle_variants' in assets and assets['obstacle_variants']:
                self.img = random.choice(assets['obstacle_variants'])
            else:
                self.img = assets['boulder']
            self.rect = pygame.Rect(x, Config.GROUND_Y - 90, 90, 90)
        elif 'dragon' in o_type:
            parts = o_type.split('_')
            height = 'low'
            color = 'red'
            for p in parts:
                if p in ('low', 'mid', 'high'): height = p
                if p in ('red', 'green', 'black'): color = p
            key = f'dragon_{color}' if f'dragon_{color}' in assets else 'dragon'
            self.frames = assets[key]
            self.frame_idx = 0
            self.img = self.frames[0]
            if assets.get('dragon_user_frames', False):
                ih = self.img.get_height(); iw = self.img.get_width()
                target_h = 64
                target_w = max(40, int(iw * (target_h / max(1, ih))))
                base = 140
                if height == 'low':
                    y_pos = Config.GROUND_Y - (target_h + base)
                elif height == 'mid':
                    y_pos = Config.GROUND_Y - (target_h + base + 60)
                else:
                    y_pos = Config.GROUND_Y - (target_h + base + 120)
                y_pos = max(0, min(y_pos, Config.SCREEN_HEIGHT - target_h - 1))
                self.rect = pygame.Rect(x, y_pos, target_w, target_h)
            else:
                y_pos = Config.GROUND_Y - 50
                if height == 'mid': y_pos = Config.GROUND_Y - 120
                if height == 'high': y_pos = Config.GROUND_Y - 190
                self.rect = pygame.Rect(x, y_pos, 80, 50)
            base_mul = 1.0 if color == 'red' else (0.95 if color == 'green' else 1.0)
            self.speed_mul = base_mul
        elif o_type == 'folder':
            # Generic ground obstacle with provided image
            self.img = data['img'] if data and 'img' in data else assets['rock']
            # Maintain aspect ratio with a reasonable on-screen visible height, compensating for transparent padding
            iw, ih = self.img.get_width(), self.img.get_height()
            # Visible bounding box from mask to detect transparent margins
            vis_mask = pygame.mask.from_surface(self.img)
            vis_rect = vis_mask.get_bounding_rects()
            if vis_rect:
                vr = vis_rect[0]
                vis_h = max(1, vr.height)
                # Scale so that VISIBLE height maps to target_h (smaller overall)
                target_h = max(28, min(72, int(vis_h * 0.75)))
                s = target_h / vis_h
                target_w = max(36, int(iw * s))
                scaled_total_h = max(10, int(ih * s))
                # Extra transparent padding at the bottom after scaling
                extra_bottom = int((ih - (vr.top + vr.height)) * s)
                # Place so the VISIBLE bottom sits on ground
                y_top = Config.GROUND_Y - (scaled_total_h - extra_bottom)
                self.rect = pygame.Rect(x, y_top, target_w, scaled_total_h)
            else:
                # Fallback if mask empty
                target_h = max(28, min(72, int(ih * 0.75)))
                s = target_h / max(1, ih)
                target_w = max(36, int(iw * s))
                self.rect = pygame.Rect(x, Config.GROUND_Y - int(ih * s), target_w, int(ih * s))
        elif o_type == 'folder_dragon':
            # Flying obstacle with provided frames (no tinting)
            frames = data['frames'] if data and 'frames' in data else assets.get('dragon', [])
            self.frames = frames if frames else assets['dragon']
            self.frame_idx = 0
            self.img = self.frames[0]
            # Altitude: always in air like dino crow (low/mid/high above ground)
            height_tag = (data.get('height') if data and 'height' in data else random.choice(['low','mid','high']))
            # Size based on image with target height (increase for visibility)
            ih, iw = self.img.get_height(), self.img.get_width()
            target_h = 64  # more visible dragon
            target_w = max(40, int(iw * (target_h / ih)))
            self.speed_mul = 0.95
            # Heights placed fully above ground
            base = 140
            if height_tag == 'low':
                y_pos = Config.GROUND_Y - (target_h + base)
            elif height_tag == 'mid':
                y_pos = Config.GROUND_Y - (target_h + base + 60)
            else: # high
                y_pos = Config.GROUND_Y - (target_h + base + 120)
            # Clamp within screen vertically
            y_pos = max(0, min(y_pos, Config.SCREEN_HEIGHT - target_h - 1))
            self.rect = pygame.Rect(x, y_pos, target_w, target_h)
            try:
                print(f"Dragon spawn at x={x}, y={y_pos}, size=({target_w},{target_h})")
            except Exception:
                pass
        # Prepare scaled image and mask for pixel-perfect collision
        self.scaled_img = pygame.transform.smoothscale(self.img, (self.rect.w, self.rect.h))
        self.mask = pygame.mask.from_surface(self.scaled_img)

    def update(self, speed):
        move_speed = speed
        if self.type == 'boulder':
            move_speed = speed * 1.3 # Rolls faster than scrolling
            self.rotation -= 10 # Spin visual
        elif 'dragon' in self.type:
            move_speed = speed * (self.speed_mul if hasattr(self, 'speed_mul') else 1.2)
            self.frame_idx += 0.15
            self.img = self.frames[int(self.frame_idx) % len(self.frames)]
            # Update scaled image and mask for dragons (animated)
            self.scaled_img = pygame.transform.smoothscale(self.img, (self.rect.w, self.rect.h))
            self.mask = pygame.mask.from_surface(self.scaled_img)

        self.x -= move_speed
        self.rect.x = int(self.x)
        # For non-animated obstacles, ensure mask exists
        if not hasattr(self, 'scaled_img') or self.scaled_img.get_size() != (self.rect.w, self.rect.h):
            self.scaled_img = pygame.transform.smoothscale(self.img, (self.rect.w, self.rect.h))
            self.mask = pygame.mask.from_surface(self.scaled_img)

    def draw(self, surf):
        if self.type == 'boulder':
            base = pygame.transform.smoothscale(self.img, (self.rect.w, self.rect.h))
            rot_img = pygame.transform.rotate(base, self.rotation)
            r = rot_img.get_rect(center=self.rect.center)
            surf.blit(rot_img, r)
        elif 'dragon' in self.type:
            scaled = pygame.transform.smoothscale(self.img, (self.rect.w, self.rect.h))
            # Outline/glow behind dragon for visibility
            try:
                out = pygame.Surface((self.rect.w+4, self.rect.h+4), pygame.SRCALPHA)
                mask = pygame.mask.from_surface(scaled)
                outline_color = (0, 0, 0, 180)
                for dx, dy in [(-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,-1),(-1,1),(1,1)]:
                    outline_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
                    mask.to_surface(outline_surf, setcolor=outline_color, unsetcolor=(0,0,0,0))
                    out.blit(outline_surf, (2+dx, 2+dy))
                surf.blit(out, (self.rect.x-2, self.rect.y-2))
            except Exception:
                pass
            # Always draw a solid silhouette from mask to guarantee visible body
            try:
                mask = pygame.mask.from_surface(scaled)
                sil = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
                mask.to_surface(sil, setcolor=(30,30,30,220), unsetcolor=(0,0,0,0))
                surf.blit(sil, (self.rect.x, self.rect.y))
                # Draw the original scaled sprite on top
                surf.blit(scaled, (self.rect.x, self.rect.y))
            except Exception:
                surf.blit(scaled, (self.rect.x, self.rect.y))
        else:
            scaled = pygame.transform.smoothscale(self.img, (self.rect.w, self.rect.h))
            surf.blit(scaled, (self.rect.x, self.rect.y))

class PowerUp:
    def __init__(self, x, assets):
        self.x = x
        # Only two tickets: BLUE and YELLOW
        self.type = random.choice(['BLUE', 'YELLOW'])
        self.y = Config.GROUND_Y - 160
        self.start_y = self.y
        self.timer = 0
        
        if self.type == 'BLUE':
            self.img = assets.get('ticket_blue')
        elif self.type == 'YELLOW':
            self.img = assets.get('ticket_yellow')
        
        # Scale for icon
        self.img = pygame.transform.scale(self.img, (40, 40))
        self.rect = pygame.Rect(x, self.y, 40, 40)

    def update(self, speed):
        self.x -= speed
        self.rect.x = int(self.x)
        
        # Bobbing motion
        self.timer += 0.1
        self.y = self.start_y + math.sin(self.timer) * 15
        self.rect.y = int(self.y)

    def draw(self, surf):
        surf.blit(self.img, (self.x, self.y))

# ==============================================================================
# 6. ENVIRONMENT (Parallax & Day/Night)
# ==============================================================================
class Environment:
    def __init__(self, assets):
        self.assets = assets
        self.cycle_timer = 0
        self.is_day = True
        self.current_sky = list(Config.COLORS['day_sky'])
        # Background images disabled for visibility
        self.bg_day = None
        self.bg_night = None
        # Blend factor for cross-fade: 1.0 = day, 0.0 = night
        self.bg_blend = 1.0
        
        # Parallax Layers: [Image, x, y, speed_factor]
        self.layers = []
        # Add 3 Pagodas spaced out
        for i in range(3):
            self.layers.append({
                'img': assets['pagoda'],
                'x': i * 400 + 100,
                'y': Config.GROUND_Y - 140,
                'speed': 0.2
            })
        self.clouds = []
        self.lanterns = []
        for i in range(4):
            self.clouds.append({'x': random.randint(0, Config.SCREEN_WIDTH), 'y': random.randint(20, 160), 'speed': 0.1 + random.random() * 0.15, 'scale': random.uniform(0.8, 1.4)})
        for i in range(3):
            self.lanterns.append({'x': random.randint(0, Config.SCREEN_WIDTH), 'y': random.randint(120, 220), 'speed': 0.12, 'img': assets['lantern']})

    def toggle_day_night(self):
        # Immediate toggle when user requests
        self.is_day = not self.is_day
        self.cycle_timer = 0

    def update(self, speed):
        # 1. Day/Night Cycle Interpolation
        self.cycle_timer += 1
        target = Config.COLORS['day_sky'] if self.is_day else Config.COLORS['night_sky']
        
        # Smoothly transition RGB values
        for i in range(3):
            if self.current_sky[i] < target[i]: self.current_sky[i] += 0.2
            elif self.current_sky[i] > target[i]: self.current_sky[i] -= 0.2
            
        # Smoothly transition background blend
        target_blend = 1.0 if self.is_day else 0.0
        if self.bg_blend < target_blend: self.bg_blend = min(target_blend, self.bg_blend + 0.02)
        elif self.bg_blend > target_blend: self.bg_blend = max(target_blend, self.bg_blend - 0.02)
        
        if self.cycle_timer > Config.NIGHT_CYCLE_FRAMES:
            self.is_day = not self.is_day
            self.cycle_timer = 0

        # 2. Update Parallax
        for layer in self.layers:
            layer['x'] -= speed * layer['speed']
            if layer['x'] < -200:
                layer['x'] = Config.SCREEN_WIDTH + random.randint(50, 300)
        for c in self.clouds:
            c['x'] -= speed * c['speed']
            if c['x'] < -120:
                c['x'] = Config.SCREEN_WIDTH + random.randint(0, 200)
                c['y'] = random.randint(30, 160)
                c['scale'] = random.uniform(0.8, 1.4)
        for l in self.lanterns:
            l['x'] -= speed * l['speed']
            if l['x'] < -50:
                l['x'] = Config.SCREEN_WIDTH + random.randint(50, 300)

    def draw(self, surf):
        # Always use color sky for maximum visibility
        surf.fill(tuple(int(c) for c in self.current_sky))
        
        # Sun / Moon
        cx, cy = 800, 100
        if self.is_day:
            pygame.draw.circle(surf, (255, 255, 200), (cx, cy), 40) # Sun
        else:
            pygame.draw.circle(surf, (220, 220, 220), (cx, cy), 30) # Moon
            pygame.draw.circle(surf, tuple(map(int, self.current_sky)), (cx - 10, cy - 5), 25) # Crescent cutout

        # Parallax Objects
        for layer in self.layers:
            surf.blit(layer['img'], (layer['x'], layer['y']))
        for c in self.clouds:
            w = int(80 * c['scale'])
            h = int(40 * c['scale'])
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            col = (255, 255, 255, 200)
            pygame.draw.ellipse(s, col, (0, 10, w-10, h-10))
            pygame.draw.ellipse(s, col, (10, 0, w-20, h-20))
            surf.blit(s, (int(c['x']), int(c['y'])))
        for l in self.lanterns:
            surf.blit(l['img'], (int(l['x']), int(l['y'])))

        # Ground
        pygame.draw.rect(surf, Config.COLORS['ground'], 
                         (0, Config.GROUND_Y, Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT - Config.GROUND_Y))
        pygame.draw.line(surf, Config.COLORS['grass'], 
                         (0, Config.GROUND_Y), (Config.SCREEN_WIDTH, Config.GROUND_Y), 4)

# ==============================================================================
# 7. GAME ENGINE (Main Class)
# ==============================================================================
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption(Config.TITLE)
        self.clock = pygame.time.Clock()
        
        # Loaders
        self.audio = AudioManager()
        self.assets = AssetLoader('images')
        self.assets.load_all()
        
        # Fonts
        self.font_main = pygame.font.SysFont("Impact", 40)
        self.font_small = pygame.font.SysFont("Arial", 20, bold=True)
        
        self.high_score = self.load_high_score()
        self.reset_game()
        self.state = "MENU" # MENU, PLAYING, GAMEOVER
        # UI: day/night toggle button
        self.toggle_rect = pygame.Rect(Config.SCREEN_WIDTH - 210, 10, 200, 28)

    def load_high_score(self):
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read())
        except:
            return 0

    def save_high_score(self):
        if int(self.score) > self.high_score:
            self.high_score = int(self.score)
            with open("highscore.txt", "w") as f:
                f.write(str(self.high_score))

    def reset_game(self):
        self.samurai = Samurai(self.assets.sprites)
        self.env = Environment(self.assets.sprites)
        self.obstacles = []
        self.powerups = []
        self.particles = []
        self.score = 0
        self.speed = Config.START_SPEED
        self.game_over_timer = 0
        self.frame_count = 0
        self.last_bamboo_frame = -999
        self.last_spawn_type = None
        self.last_bamboo_x = -99999
        self.debug_hitboxes = False
        # Dragon timing control
        self.first_dragon_spawned = False

    def spawn_logic(self):
        # Obstacles
        if not self.obstacles or self.obstacles[-1].x < Config.SCREEN_WIDTH - random.randint(400, 800):
            # Global minimum gap from the last obstacle on screen
            min_gap_px = 140
            last_x = self.obstacles[-1].x if self.obstacles else -9999
            spawn_x = max(Config.SCREEN_WIDTH, last_x + min_gap_px)
            # Ensure an early first dragon if user provided one
            if (not self.first_dragon_spawned) and self.frame_count >= 60:
                dpool = self.assets.sprites.get('strict_dragons') or self.assets.sprites.get('folder_dragons') or []
                if dpool:
                    data = random.choice(dpool)
                    self.obstacles.append(Obstacle(spawn_x, 'folder_dragon', self.assets.sprites, data))
                    self.first_dragon_spawned = True
                    self.last_spawn_type = 'folder_dragon'
                    return
            # STRICT mode from images/ root or folder pools
            if self.assets.sprites.get('strict_mode', False):
                gpool = self.assets.sprites.get('strict_ground', [])
                dpool = self.assets.sprites.get('strict_dragons', [])
                if gpool or dpool:
                    # If both exist, give dragons ~30% chance
                    if gpool and dpool:
                        if random.random() < 0.30:
                            data = random.choice(dpool)
                            self.obstacles.append(Obstacle(spawn_x, 'folder_dragon', self.assets.sprites, data))
                            self.last_spawn_type = 'folder_dragon'
                            self.first_dragon_spawned = True
                            try:
                                print("Spawned dragon from strict images pool")
                            except Exception:
                                pass
                        else:
                            data = random.choice(gpool)
                            self.obstacles.append(Obstacle(spawn_x, 'folder', self.assets.sprites, data))
                            self.last_spawn_type = 'folder'
                    elif dpool:
                        data = random.choice(dpool)
                        self.obstacles.append(Obstacle(spawn_x, 'folder_dragon', self.assets.sprites, data))
                        self.last_spawn_type = 'folder_dragon'
                        self.first_dragon_spawned = True
                        try:
                            print("Spawned dragon from strict images pool")
                        except Exception:
                            pass
                    else:
                        data = random.choice(gpool)
                        self.obstacles.append(Obstacle(spawn_x, 'folder', self.assets.sprites, data))
                        self.last_spawn_type = 'folder'
                    return
            # Folder mode: if user placed obstacles in images/obstacles or images/obatcles
            folder_obs = self.assets.sprites.get('folder_obstacles', [])
            folder_drag = self.assets.sprites.get('folder_dragons', [])
            if folder_obs or folder_drag:
                pool = []
                pool.extend([('folder', o) for o in folder_obs])
                pool.extend([('folder_dragon', d) for d in folder_drag])
                kind, data = random.choice(pool)
                if kind == 'folder':
                    self.obstacles.append(Obstacle(spawn_x, 'folder', self.assets.sprites, data))
                    self.last_spawn_type = 'folder'
                else:
                    self.obstacles.append(Obstacle(spawn_x, 'folder_dragon', self.assets.sprites, data))
                    self.last_spawn_type = 'folder_dragon'
            else:
                # Default weighted mix
                r = random.random()
                if r < 0.25:
                    type_ = 'rock'
                    self.obstacles.append(Obstacle(spawn_x, type_, self.assets.sprites))
                    self.last_spawn_type = 'rock'
                elif r < 0.45:
                    type_ = 'barrel'
                    self.obstacles.append(Obstacle(spawn_x, type_, self.assets.sprites))
                    self.last_spawn_type = 'barrel'
                elif r < 0.65 and self.last_spawn_type != 'bamboo':
                    # Bamboo cooldowns
                    bamboo_frame_cooldown = 240
                    bamboo_px_cooldown = 300
                    can_bamboo_time = (self.frame_count - self.last_bamboo_frame) > bamboo_frame_cooldown
                    can_bamboo_dist = (spawn_x - self.last_bamboo_x) > bamboo_px_cooldown
                    if can_bamboo_time and can_bamboo_dist:
                        self.obstacles.append(Obstacle(spawn_x, 'bamboo', self.assets.sprites))
                        self.last_bamboo_frame = self.frame_count
                        self.last_bamboo_x = spawn_x
                        self.last_spawn_type = 'bamboo'
                    else:
                        self.obstacles.append(Obstacle(spawn_x, 'rock', self.assets.sprites))
                        self.last_spawn_type = 'rock'
                elif r < 0.9:
                    h = random.choice(['low', 'mid', 'high'])
                    color = random.choices(['red', 'green', 'black'], weights=[5, 4, 1])[0]
                    type_ = f'dragon_{h}_{color}'
                    self.obstacles.append(Obstacle(spawn_x, type_, self.assets.sprites))
                    self.last_spawn_type = 'dragon'
                else:
                    if self.assets.sprites.get('boulder_image_available', False):
                        type_ = 'boulder'
                    else:
                        type_ = 'rock'
                    self.obstacles.append(Obstacle(spawn_x, type_, self.assets.sprites))
                    self.last_spawn_type = type_

        # Powerups (Rare)
        if random.random() < 0.003:
            self.powerups.append(PowerUp(Config.SCREEN_WIDTH, self.assets.sprites))

        # Ambient Particles
        if self.env.is_day and random.random() < 0.1:
            self.particles.append(Particle(random.randint(0, Config.SCREEN_WIDTH), -10, 'petal'))
        elif not self.env.is_day and random.random() < 0.05:
            self.particles.append(Particle(random.randint(0, Config.SCREEN_WIDTH), Config.SCREEN_HEIGHT, 'sparkle'))

    def update(self):
        # 1. Update Score & Speed
        self.score += Config.SCORE_PER_FRAME
        if int(self.score) % 100 == 0 and int(self.score) > 0:
            self.audio.play('score')
        
        self.speed = min(Config.MAX_SPEED, self.speed + Config.SPEED_INCREMENT)
        # Effective speed (dash boost ~25%)
        eff_speed = self.speed * (1.25 if self.samurai.dash_timer > 0 else 1.0)
        self.frame_count += 1

        # 2. Update Entities
        self.env.update(eff_speed)
        self.samurai.update()
        if not self.samurai.is_jumping and not self.samurai.is_ducking and self.frame_count % 12 == 0:
            self.particles.append(Particle(self.samurai.x, self.samurai.y + 80, 'dust'))
        
        self.spawn_logic()

        # 3. Update Lists
        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        for p in self.powerups: p.update(eff_speed)
        # Cleanup Powerups
        self.powerups = [p for p in self.powerups if p.x > -100]

        for obs in self.obstacles:
            obs.update(eff_speed)
        # Cleanup Obstacles
        self.obstacles = [o for o in self.obstacles if o.x > -200]

        # 3.5 Tornado auto-destroys next obstacle ahead (single-use)
        if self.samurai.tornado_ready and self.obstacles:
            ahead = [o for o in self.obstacles if o.x > self.samurai.x + 20]
            if ahead:
                target = ahead[0]
                self.obstacles.remove(target)
                self.audio.play('slash')
                self.score += 50
                for _ in range(8):
                    self.particles.append(Particle(target.x, target.rect.y, 'debris'))
                self.samurai.tornado_ready = False

        # 4. Collision Detection
        player_rect = self.samurai.get_hitbox()

        # Powerup Collision
        for p in self.powerups[:]:
            if player_rect.colliderect(p.rect):
                self.samurai.activate_powerup(p.type, self.audio)
                self.powerups.remove(p)
                # Burst effect
                for _ in range(10):
                    self.particles.append(Particle(self.samurai.x, self.samurai.y, 'sparkle'))

        # Obstacle Collision (pixel-perfect)
        sam_surf, sam_rect = self.samurai.get_surface_and_rect()
        sam_mask = pygame.mask.from_surface(sam_surf)
        for obs in self.obstacles[:]:
            if obs.rect.right <= 0 or obs.rect.left >= Config.SCREEN_WIDTH:
                continue
            if not sam_rect.colliderect(obs.rect):
                continue
            offset = (obs.rect.x - sam_rect.x, obs.rect.y - sam_rect.y)
            if getattr(obs, 'mask', None) is None:
                obs.scaled_img = pygame.transform.smoothscale(obs.img, (obs.rect.w, obs.rect.h))
                obs.mask = pygame.mask.from_surface(obs.scaled_img)
            if sam_mask.overlap(obs.mask, offset):
                # Collision occurs: handle normally
                # Tornado single-use if still ready on collision
                if self.samurai.tornado_ready:
                    if obs in self.obstacles:
                        self.obstacles.remove(obs)
                    self.audio.play('slash')
                    self.score += 50
                    for _ in range(8):
                        self.particles.append(Particle(obs.x, obs.rect.y, 'debris'))
                    self.samurai.tornado_ready = False
                # Dash: invulnerable, pass through
                elif self.samurai.dash_timer > 0:
                    pass
                else:
                    self.audio.play('hit')
                    self.state = "GAMEOVER"
                    self.save_high_score()

    def draw_text_centered(self, text, font, y_offset, color=(255, 255, 255)):
        s = font.render(text, True, color)
        rect = s.get_rect(center=(Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2 + y_offset))
        # Shadow
        s_shadow = font.render(text, True, (0,0,0))
        self.screen.blit(s_shadow, (rect.x+2, rect.y+2))
        self.screen.blit(s, rect)

    def draw(self):
        # Draw World
        self.env.draw(self.screen)
        
        for p in self.powerups: p.draw(self.screen)
        # Draw ground obstacles first, dragons later for top visibility
        for obs in self.obstacles:
            if 'dragon' not in obs.type:
                obs.draw(self.screen)
        for part in self.particles: part.draw(self.screen)
        # Draw dragons on top
        for obs in self.obstacles:
            if 'dragon' in obs.type:
                obs.draw(self.screen)
        
        self.samurai.draw(self.screen)

        # Debug: draw hitboxes
        if self.debug_hitboxes:
            # Player
            pygame.draw.rect(self.screen, (0,255,0), self.samurai.get_hitbox(), 2)
            # Obstacles
            for obs in self.obstacles:
                # Per-type shrink preview (matches collision below)
                if obs.type == 'bamboo':
                    hb = obs.rect.inflate(-16, -10)
                elif obs.type == 'boulder':
                    hb = obs.rect.inflate(-12, -12)
                elif 'dragon' in obs.type:
                    hb = obs.rect.inflate(-18, -12)
                else:
                    hb = obs.rect.inflate(-18, -18)
                pygame.draw.rect(self.screen, (255,0,0), hb, 2)

        # Draw HUD
        score_txt = self.font_small.render(f"SCORE: {int(self.score)}", True, Config.COLORS['text'])
        high_txt = self.font_small.render(f"HI: {self.high_score}", True, (200, 200, 200))
        self.screen.blit(score_txt, (20, 20))
        self.screen.blit(high_txt, (20, 50))
        
        # Toggle Day/Night button (top-right)
        pygame.draw.rect(self.screen, (0,0,0), self.toggle_rect, border_radius=6)
        pygame.draw.rect(self.screen, (230,230,230), self.toggle_rect.inflate(-2, -2), border_radius=6)
        label = "Toggle Day/Night (T)"
        txt = self.font_small.render(label, True, (20,20,20))
        tr = txt.get_rect(center=self.toggle_rect.center)
        self.screen.blit(txt, tr)
        
        # Status: Tornado ready indicator
        if self.samurai.tornado_ready:
            self.screen.blit(self.font_small.render("TORNADO READY", True, (255,120,120)), (20, 80))
        # Dash bar (remaining frames)
        if self.samurai.dash_timer > 0:
            bar_w = int(self.samurai.dash_timer * 1.2)
            pygame.draw.rect(self.screen, (100, 200, 255), (20, 100, bar_w, 10))
            self.screen.blit(self.font_small.render("DASH", True, (100,200,255)), (25, 95))

        # Menus
        if self.state == "MENU":
            # Darken bg
            overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0,0,0))
            self.screen.blit(overlay, (0,0))
            
            self.draw_text_centered(Config.TITLE, self.font_main, -50, (255, 215, 0))
            self.draw_text_centered("Press SPACE to Start", self.font_small, 20)
            self.draw_text_centered("Arrows: Jump/Duck | Collect Items for Powerups", self.font_small, 60, (200,200,200))

        elif self.state == "GAMEOVER":
            overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((50,0,0)) # Red tint
            self.screen.blit(overlay, (0,0))
            
            self.draw_text_centered("HONOR LOST", self.font_main, -40, (255, 50, 50))
            self.draw_text_centered(f"Final Score: {int(self.score)}", self.font_small, 10)
            self.draw_text_centered("Press SPACE to Retry", self.font_small, 50)

        pygame.display.flip()

    def run(self):
        while True:
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_h:
                        self.debug_hitboxes = not self.debug_hitboxes
                    if event.key == pygame.K_t:
                        self.env.toggle_day_night()
                    if event.key == pygame.K_g:
                        if self.state == "PLAYING":
                            # Force-spawn a dragon just off-screen to the right for testing
                            spawn_x = Config.SCREEN_WIDTH + 10
                            dpool = self.assets.sprites.get('strict_dragons') or self.assets.sprites.get('folder_dragons') or []
                            if dpool:
                                data = random.choice(dpool)
                                self.obstacles.append(Obstacle(spawn_x, 'folder_dragon', self.assets.sprites, data))
                            else:
                                # Fallback to root dragon frames
                                frames = self.assets.sprites.get('dragon', None)
                                if frames:
                                    self.obstacles.append(Obstacle(spawn_x, 'folder_dragon', self.assets.sprites, {'frames': frames}))
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                        if self.state == "MENU":
                            self.state = "PLAYING"
                            self.reset_game()
                            self.samurai.jump(self.audio)
                        elif self.state == "GAMEOVER":
                            self.state = "PLAYING"
                            self.reset_game()
                        elif self.state == "PLAYING":
                            effect = self.samurai.jump(self.audio)
                            if effect == 'dust':
                                for _ in range(3): self.particles.append(Particle(self.samurai.x, self.samurai.y+80, 'dust'))
                            elif effect == 'sparkle':
                                for _ in range(5): self.particles.append(Particle(self.samurai.x, self.samurai.y+40, 'sparkle'))
                                
                    if event.key == pygame.K_DOWN:
                        if self.state == "PLAYING":
                            self.samurai.duck(True)
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_DOWN:
                        if self.state == "PLAYING":
                            self.samurai.duck(False)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.toggle_rect.collidepoint(event.pos):
                        self.env.toggle_day_night()

            # Loop
            if self.state == "PLAYING":
                self.update()
            
            self.draw()
            self.clock.tick(Config.FPS)

if __name__ == '__main__':
    Game().run()
