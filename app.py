import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string
import time
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'word-bomb-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

rooms = {}
players = {}
timers = {}

INITIAL_LIVES = 2
TURN_TIME = 15
MIN_PLAYERS = 2
MAX_PLAYERS = 16

WORDS_FILE = os.path.join(os.path.dirname(__file__), "words.txt")

def load_word_list():
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        dwyl_words = f.read().splitlines()
    common_words = set([
        'about', 'above', 'abuse', 'accept', 'accident', 'account', 'across', 'action', 'active', 'actor',
        'actual', 'adapt', 'added', 'admit', 'adopt', 'adult', 'advance', 'advice', 'affair', 'affect',
        'afford', 'afraid', 'after', 'again', 'against', 'agency', 'agent', 'agree', 'ahead', 'alarm',
        'album', 'alcohol', 'alive', 'allow', 'almost', 'alone', 'along', 'already', 'also', 'alter',
        'always', 'amount', 'ancient', 'anger', 'angle', 'angry', 'animal', 'annual', 'another', 'answer',
        'anyone', 'anyway', 'apart', 'apparent', 'appeal', 'appear', 'apple', 'apply', 'approach', 'approve',
        'area', 'argue', 'arise', 'armed', 'army', 'around', 'arrange', 'arrest', 'arrive', 'article',
        'artist', 'aspect', 'assault', 'assert', 'assess', 'asset', 'assign', 'assist', 'assume', 'assure',
        'attach', 'attack', 'attempt', 'attend', 'attract', 'author', 'auto', 'available', 'average', 'avoid',
        'award', 'aware', 'baby', 'back', 'background', 'ball', 'band', 'bank', 'base', 'basic',
        'basis', 'battle', 'beach', 'bear', 'beat', 'beautiful', 'because', 'become', 'been', 'before',
        'begin', 'behavior', 'behind', 'being', 'belief', 'believe', 'bell', 'belong', 'below', 'bench',
        'bend', 'beneath', 'benefit', 'beside', 'best', 'better', 'between', 'beyond', 'bike', 'bill',
        'bind', 'bird', 'birth', 'bite', 'bitter', 'black', 'blade', 'blame', 'blank', 'blind',
        'block', 'blood', 'blow', 'blue', 'board', 'boat', 'body', 'boil', 'bold', 'bomb',
        'bond', 'bone', 'book', 'boom', 'boot', 'border', 'born', 'boss', 'both', 'bother',
        'bottle', 'bottom', 'bound', 'bowl', 'brain', 'branch', 'brand', 'brave', 'bread', 'break',
        'breakfast', 'breath', 'breathe', 'breed', 'bridge', 'brief', 'bright', 'bring', 'broad', 'broken',
        'brother', 'brown', 'brush', 'budget', 'build', 'building', 'bunch', 'burn', 'burst', 'bury',
        'business', 'busy', 'butter', 'button', 'cake', 'call', 'calm', 'camera', 'camp', 'campaign',
        'cancel', 'cancer', 'candidate', 'capacity', 'capital', 'captain', 'capture', 'carbon', 'card', 'care',
        'career', 'careful', 'carry', 'case', 'cash', 'cast', 'catch', 'category', 'cause', 'ceiling',
        'celebrate', 'cell', 'center', 'central', 'century', 'ceremony', 'certain', 'chain', 'chair', 'challenge',
        'chamber', 'champion', 'chance', 'change', 'channel', 'chapter', 'character', 'charge', 'charity', 'chart',
        'chase', 'cheap', 'check', 'cheese', 'chemical', 'chest', 'chicken', 'chief', 'child', 'childhood',
        'choice', 'choose', 'church', 'circle', 'citizen', 'city', 'civil', 'claim', 'class', 'classic',
        'clean', 'clear', 'client', 'climate', 'climb', 'clock', 'close', 'closet', 'cloth', 'cloud',
        'club', 'coach', 'coast', 'coat', 'code', 'coffee', 'cold', 'collapse', 'collect', 'college',
        'color', 'column', 'combine', 'come', 'comfort', 'command', 'comment', 'commit', 'common', 'communicate',
        'community', 'company', 'compare', 'compete', 'complain', 'complete', 'complex', 'computer', 'concentrate', 'concept',
        'concern', 'concert', 'conclude', 'concrete', 'condition', 'conduct', 'conference', 'confess', 'confidence', 'confirm',
        'conflict', 'confront', 'confuse', 'connect', 'consider', 'consist', 'constant', 'construct', 'consult', 'consumer',
        'contact', 'contain', 'contemporary', 'content', 'contest', 'context', 'continue', 'contract', 'contrast', 'contribute',
        'control', 'convention', 'conversation', 'convert', 'convince', 'cook', 'cool', 'cope', 'copy', 'core',
        'corner', 'corporate', 'correct', 'cost', 'cotton', 'couch', 'could', 'council', 'count', 'counter',
        'country', 'county', 'couple', 'courage', 'course', 'court', 'cousin', 'cover', 'crack', 'craft',
        'crash', 'crazy', 'cream', 'create', 'credit', 'crew', 'crime', 'criminal', 'crisis', 'critic',
        'critical', 'crop', 'cross', 'crowd', 'crucial', 'cruel', 'crush', 'culture', 'curious', 'current',
        'curve', 'custom', 'customer', 'cycle', 'daily', 'damage', 'dance', 'danger', 'dare', 'dark',
        'data', 'date', 'daughter', 'dead', 'deal', 'dealer', 'dear', 'death', 'debate', 'debt',
        'decade', 'decide', 'decision', 'declare', 'decline', 'decorate', 'decrease', 'deep', 'defeat', 'defend',
        'defense', 'deficit', 'define', 'definitely', 'degree', 'delay', 'deliver', 'delivery', 'demand', 'democracy',
        'demonstrate', 'deny', 'department', 'depend', 'depict', 'deposit', 'depress', 'depth', 'derive', 'describe',
        'desert', 'deserve', 'design', 'designer', 'desire', 'desk', 'desperate', 'despite', 'destroy', 'detail',
        'detect', 'determine', 'develop', 'device', 'devote', 'dialogue', 'diamond', 'diary', 'diet', 'differ',
        'difference', 'different', 'difficult', 'digital', 'dimension', 'dinner', 'direct', 'direction', 'director', 'dirt',
        'dirty', 'disabled', 'disagree', 'disappear', 'disaster', 'discipline', 'discover', 'discuss', 'disease', 'dish',
        'dismiss', 'disorder', 'display', 'dispute', 'distance', 'distinct', 'distinguish', 'distribute', 'district', 'diverse',
        'divide', 'division', 'divorce', 'doctor', 'document', 'domestic', 'dominant', 'dominate', 'door', 'double',
        'doubt', 'down', 'downtown', 'dozen', 'draft', 'drag', 'drama', 'dramatic', 'draw', 'drawer',
        'dream', 'dress', 'drink', 'drive', 'driver', 'drop', 'drug', 'during', 'dust', 'duty',
        'each', 'eager', 'early', 'earn', 'earth', 'ease', 'easily', 'east', 'eastern', 'easy',
        'economic', 'economy', 'edge', 'edit', 'editor', 'educate', 'education', 'effect', 'effective', 'efficiency',
        'efficient', 'effort', 'eight', 'either', 'elderly', 'elect', 'election', 'electric', 'element', 'eliminate',
        'elite', 'else', 'elsewhere', 'emerge', 'emergency', 'emission', 'emotion', 'emotional', 'emphasis', 'emphasize',
        'employ', 'employee', 'employer', 'empty', 'enable', 'encounter', 'encourage', 'enemy', 'energy', 'enforce',
        'engage', 'engine', 'engineer', 'enhance', 'enjoy', 'enormous', 'enough', 'ensure', 'enter', 'enterprise',
        'entertain', 'entire', 'entirely', 'entrance', 'entry', 'environment', 'equal', 'equipment', 'error', 'escape',
        'especially', 'essay', 'essential', 'establish', 'estate', 'estimate', 'ethical', 'ethnic', 'evaluate', 'even',
        'evening', 'event', 'eventually', 'ever', 'every', 'everybody', 'everyday', 'everyone', 'everything', 'everywhere',
        'evidence', 'evil', 'evolve', 'exact', 'exactly', 'exam', 'examine', 'example', 'exceed', 'excellent',
        'except', 'exception', 'exchange', 'excite', 'exclude', 'executive', 'exercise', 'exhibit', 'exist', 'exit',
        'expand', 'expect', 'expense', 'expensive', 'experience', 'experiment', 'expert', 'explain', 'explode', 'explore',
        'explosion', 'expose', 'express', 'extend', 'extension', 'extensive', 'extent', 'external', 'extra', 'extreme',
        'face', 'facility', 'fact', 'factor', 'factory', 'faculty', 'fade', 'fail', 'failure', 'fair',
        'faith', 'fall', 'false', 'familiar', 'family', 'famous', 'fantasy', 'fare', 'farm', 'farmer',
        'fashion', 'fast', 'fatal', 'father', 'fault', 'favor', 'favorite', 'fear', 'feature', 'federal',
        'feed', 'feel', 'feeling', 'fellow', 'female', 'fence', 'festival', 'fetch', 'fever', 'fiber',
        'fiction', 'field', 'fifteen', 'fifth', 'fifty', 'fight', 'fighter', 'figure', 'file', 'fill',
        'film', 'final', 'finally', 'finance', 'financial', 'find', 'finding', 'fine', 'finger', 'finish',
        'fire', 'firm', 'first', 'fish', 'fishing', 'fitness', 'five', 'fixed', 'flag', 'flame',
        'flash', 'flat', 'flavor', 'flee', 'flesh', 'flexible', 'flight', 'float', 'floor', 'flow',
        'flower', 'fluid', 'focus', 'folk', 'follow', 'food', 'foot', 'football', 'force', 'foreign',
        'forest', 'forever', 'forget', 'form', 'formal', 'format', 'former', 'formula', 'forth', 'fortune',
        'forum', 'forward', 'found', 'foundation', 'founder', 'four', 'fourth', 'frame', 'framework', 'free',
        'freedom', 'freeze', 'french', 'frequency', 'frequent', 'fresh', 'friend', 'friendly', 'friendship', 'frighten',
        'from', 'front', 'fruit', 'frustrate', 'fuel', 'full', 'fully', 'function', 'fund', 'fundamental',
        'funding', 'funeral', 'funny', 'furniture', 'furthermore', 'future', 'gain', 'galaxy', 'gallery', 'game',
        'gang', 'garden', 'garlic', 'gate', 'gather', 'gaze', 'gear', 'gender', 'gene', 'general',
        'generate', 'generation', 'generous', 'genetic', 'genius', 'genre', 'gentle', 'gentleman', 'genuine', 'gesture',
        'gift', 'girl', 'girlfriend', 'give', 'glad', 'glance', 'glass', 'global', 'glove', 'goal',
        'gold', 'golden', 'golf', 'good', 'government', 'governor', 'grab', 'grade', 'gradually', 'graduate',
        'grain', 'grand', 'grandfather', 'grandmother', 'grant', 'grass', 'grave', 'gray', 'great', 'green',
        'greet', 'grid', 'grief', 'ground', 'group', 'grow', 'growth', 'guarantee', 'guard', 'guess',
        'guest', 'guide', 'guilty', 'guitar', 'half', 'hall', 'hand', 'handful', 'handle', 'hang',
        'happen', 'happy', 'hard', 'hardly', 'harm', 'hate', 'have', 'head', 'headline', 'headquarters',
        'health', 'healthy', 'hear', 'hearing', 'heart', 'heat', 'heaven', 'heavily', 'heavy', 'heel',
        'height', 'helicopter', 'hell', 'hello', 'help', 'helpful', 'heritage', 'hero', 'herself', 'hesitate',
        'hide', 'high', 'highlight', 'highly', 'highway', 'hill', 'himself', 'hire', 'historian', 'historic',
        'historical', 'history', 'hold', 'hole', 'holiday', 'holy', 'home', 'homeless', 'honest', 'honey',
        'honor', 'hope', 'horizon', 'horror', 'horse', 'hospital', 'host', 'hotel', 'hour', 'house',
        'household', 'housing', 'however', 'huge', 'human', 'humor', 'hundred', 'hungry', 'hunter', 'hunting',
        'hurry', 'hurt', 'husband', 'hypothesis', 'idea', 'ideal', 'identify', 'identity', 'ignore', 'illegal',
        'illness', 'illustrate', 'image', 'imagination', 'imagine', 'immediate', 'immigrant', 'impact', 'implement', 'implication',
        'imply', 'import', 'importance', 'important', 'impose', 'impossible', 'impress', 'improve', 'incentive', 'incident',
        'include', 'income', 'incorporate', 'increase', 'increased', 'increasingly', 'incredible', 'indeed', 'independence', 'independent',
        'index', 'indicate', 'individual', 'industrial', 'industry', 'infant', 'infect', 'inflation', 'influence', 'inform',
        'information', 'ingredient', 'initial', 'initially', 'initiative', 'injury', 'inner', 'innocent', 'innovation', 'input',
        'inquiry', 'inside', 'insight', 'insist', 'inspire', 'install', 'instance', 'instead', 'institution', 'instruction',
        'instructor', 'instrument', 'insurance', 'intellectual', 'intelligence', 'intend', 'intense', 'intensity', 'intention', 'interact',
        'interest', 'interesting', 'internal', 'international', 'internet', 'interpret', 'intervention', 'interview', 'into', 'introduce',
        'invasion', 'invest', 'investigate', 'investment', 'investor', 'invite', 'involve', 'involved', 'iron', 'island',
        'isolate', 'issue', 'item', 'itself', 'jacket', 'jail', 'japanese', 'joint', 'joke', 'journal',
        'journalist', 'journey', 'judge', 'judgment', 'juice', 'jump', 'junior', 'jury', 'just', 'justice',
        'justify', 'keep', 'kick', 'kill', 'killer', 'killing', 'kind', 'king', 'kiss', 'kitchen',
        'knee', 'knife', 'knock', 'know', 'knowledge', 'label', 'labor', 'laboratory', 'lack', 'lady',
        'lake', 'land', 'landscape', 'language', 'large', 'largely', 'last', 'late', 'later', 'latin',
        'latter', 'laugh', 'launch', 'lawn', 'lawsuit', 'lawyer', 'layer', 'lead', 'leader', 'leadership',
        'leading', 'leaf', 'league', 'lean', 'learn', 'learning', 'least', 'leather', 'leave', 'left',
        'legacy', 'legal', 'legend', 'legislation', 'legitimate', 'lemon', 'length', 'less', 'lesson', 'letter',
        'level', 'liberal', 'library', 'license', 'life', 'lifestyle', 'lifetime', 'lift', 'light', 'like',
        'likely', 'limit', 'line', 'link', 'lion', 'list', 'listen', 'literally', 'literary', 'literature',
        'little', 'live', 'living', 'load', 'loan', 'local', 'locate', 'location', 'lock', 'long',
        'look', 'loose', 'lose', 'loss', 'lost', 'loud', 'love', 'lovely', 'lover', 'lower',
        'luck', 'lucky', 'lunch', 'lung', 'machine', 'magazine', 'magic', 'mail', 'main', 'mainly',
        'maintain', 'maintenance', 'major', 'majority', 'make', 'maker', 'makeup', 'male', 'mall', 'manage',
        'management', 'manager', 'manner', 'manufacturer', 'manufacturing', 'many', 'margin', 'mark', 'market', 'marketing',
        'marriage', 'married', 'marry', 'mask', 'mass', 'massive', 'master', 'match', 'material', 'math',
        'matter', 'maximum', 'maybe', 'mayor', 'meal', 'mean', 'meaning', 'meanwhile', 'measure', 'meat',
        'mechanism', 'media', 'medical', 'medicine', 'medium', 'meet', 'meeting', 'member', 'membership', 'memory',
        'mental', 'mention', 'menu', 'mere', 'merely', 'merge', 'mess', 'message', 'metal', 'meter',
        'method', 'middle', 'might', 'military', 'milk', 'mill', 'million', 'mind', 'mine', 'minimum',
        'minister', 'minor', 'minority', 'minute', 'miracle', 'mirror', 'miss', 'missile', 'mission', 'mistake',
        'mixed', 'mixture', 'mobile', 'mode', 'model', 'moderate', 'modern', 'modest', 'modify', 'moment',
        'money', 'monitor', 'month', 'mood', 'moon', 'moral', 'more', 'moreover', 'morning', 'mortgage',
        'most', 'mostly', 'mother', 'motion', 'motivate', 'motivation', 'motor', 'mount', 'mountain', 'mouse',
        'mouth', 'move', 'movement', 'movie', 'much', 'multiple', 'murder', 'muscle', 'museum', 'music',
        'musical', 'musician', 'must', 'mutual', 'myself', 'mystery', 'myth', 'naked', 'name', 'narrative',
        'narrow', 'nation', 'national', 'native', 'natural', 'naturally', 'nature', 'naval', 'navy', 'near',
        'nearby', 'nearly', 'necessarily', 'necessary', 'neck', 'need', 'negative', 'negotiate', 'neighbor', 'neighborhood',
        'neither', 'nerve', 'nervous', 'nest', 'network', 'neutral', 'never', 'nevertheless', 'newly', 'news',
        'newspaper', 'next', 'nice', 'night', 'nine', 'nobody', 'noise', 'none', 'nonetheless', 'normal',
        'normally', 'north', 'northern', 'nose', 'note', 'nothing', 'notice', 'notion', 'novel', 'nuclear',
        'number', 'numerous', 'nurse', 'object', 'objective', 'obligation', 'observation', 'observe', 'observer', 'obtain',
        'obvious', 'obviously', 'occasion', 'occasionally', 'occupy', 'occur', 'ocean', 'odds', 'offense', 'offensive',
        'offer', 'office', 'officer', 'official', 'often', 'okay', 'once', 'ongoing', 'onion', 'online',
        'only', 'onto', 'open', 'opening', 'operate', 'operating', 'operation', 'operator', 'opinion', 'opponent',
        'opportunity', 'oppose', 'opposite', 'opposition', 'option', 'orange', 'order', 'ordinary', 'organic', 'organization',
        'organize', 'orientation', 'origin', 'original', 'originally', 'other', 'others', 'otherwise', 'ought', 'outcome',
        'outside', 'oven', 'over', 'overall', 'overcome', 'overlook', 'owe', 'owner', 'pace', 'pack',
        'package', 'page', 'pain', 'painful', 'paint', 'painter', 'painting', 'pair', 'pale', 'palm',
        'panel', 'pant', 'paper', 'parent', 'park', 'parking', 'part', 'participant', 'participate', 'particular',
        'particularly', 'partly', 'partner', 'partnership', 'party', 'pass', 'passage', 'passenger', 'passion', 'past',
        'patch', 'path', 'patient', 'pattern', 'pause', 'payment', 'peace', 'peak', 'peer', 'penalty',
        'people', 'pepper', 'perceive', 'percent', 'percentage', 'perception', 'perfect', 'perform', 'performance', 'perhaps',
        'period', 'permanent', 'permission', 'permit', 'person', 'personal', 'personality', 'personally', 'personnel', 'perspective',
        'persuade', 'phase', 'phenomenon', 'philosophy', 'phone', 'photo', 'photograph', 'photographer', 'phrase', 'physical',
        'physically', 'physician', 'piano', 'pick', 'picture', 'piece', 'pile', 'pilot', 'pine', 'pink',
        'pipe', 'pitch', 'place', 'plan', 'plane', 'planet', 'planning', 'plant', 'plastic', 'plate',
        'platform', 'play', 'player', 'please', 'pleasure', 'plenty', 'plot', 'plus', 'pocket', 'poem',
        'poet', 'poetry', 'point', 'pole', 'police', 'policy', 'political', 'politically', 'politician', 'politics',
        'poll', 'pollution', 'pool', 'poor', 'popular', 'population', 'porch', 'port', 'portion', 'portrait',
        'portray', 'pose', 'position', 'positive', 'possess', 'possibility', 'possible', 'possibly', 'post', 'potato',
        'potential', 'potentially', 'pound', 'pour', 'poverty', 'powder', 'power', 'powerful', 'practical', 'practice',
        'pray', 'prayer', 'predict', 'prefer', 'preference', 'pregnant', 'preparation', 'prepare', 'prescription', 'presence',
        'present', 'presentation', 'preserve', 'president', 'presidential', 'press', 'pressure', 'pretend', 'pretty', 'prevent',
        'previous', 'previously', 'price', 'pride', 'priest', 'primarily', 'primary', 'prime', 'principal', 'principle',
        'print', 'prior', 'priority', 'prison', 'prisoner', 'privacy', 'private', 'probably', 'problem', 'procedure',
        'proceed', 'process', 'produce', 'producer', 'product', 'production', 'profession', 'professional', 'professor', 'profile',
        'profit', 'program', 'progress', 'project', 'prominent', 'promise', 'promote', 'prompt', 'proof', 'proper',
        'properly', 'property', 'proportion', 'proposal', 'propose', 'proposed', 'prosecutor', 'prospect', 'protect', 'protection',
        'protein', 'protest', 'proud', 'prove', 'provide', 'provider', 'province', 'provision', 'psychological', 'psychologist',
        'psychology', 'public', 'publication', 'publicly', 'publish', 'publisher', 'pull', 'pump', 'punish', 'punishment',
        'purchase', 'pure', 'purpose', 'pursue', 'push', 'qualification', 'qualify', 'quality', 'quarter', 'quarterback',
        'queen', 'question', 'quick', 'quickly', 'quiet', 'quietly', 'quit', 'quite', 'quote', 'race',
        'racial', 'radical', 'radio', 'rail', 'rain', 'raise', 'range', 'rank', 'rapid', 'rapidly',
        'rare', 'rarely', 'rate', 'rather', 'rating', 'ratio', 'rational', 'reach', 'react', 'reaction',
        'read', 'reader', 'reading', 'ready', 'real', 'reality', 'realize', 'really', 'reason', 'reasonable',
        'recall', 'receive', 'recent', 'recently', 'recipe', 'recognition', 'recognize', 'recommend', 'recommendation', 'record',
        'recording', 'recover', 'recovery', 'recruit', 'reduce', 'reduction', 'refer', 'reference', 'reflect', 'reflection',
        'reform', 'refugee', 'refuse', 'regard', 'regarding', 'regardless', 'regime', 'region', 'regional', 'register',
        'regular', 'regularly', 'regulate', 'regulation', 'reinforce', 'reject', 'relate', 'relation', 'relationship', 'relative',
        'relatively', 'relax', 'release', 'relevant', 'relief', 'religion', 'religious', 'rely', 'remain', 'remaining',
        'remarkable', 'remember', 'remind', 'remote', 'remove', 'repeat', 'repeatedly', 'replace', 'reply', 'report',
        'reporter', 'represent', 'representation', 'representative', 'republic', 'republican', 'reputation', 'request', 'require', 'requirement',
        'research', 'researcher', 'resemble', 'reservation', 'resident', 'resist', 'resistance', 'resolution', 'resolve', 'resort',
        'resource', 'respect', 'respond', 'respondent', 'response', 'responsibility', 'responsible', 'rest', 'restaurant', 'restore',
        'restriction', 'result', 'retain', 'retire', 'retirement', 'return', 'reveal', 'revenue', 'review', 'revolution',
        'rhythm', 'rice', 'rich', 'ride', 'rifle', 'right', 'ring', 'rise', 'risk', 'river',
        'road', 'rock', 'role', 'roll', 'romantic', 'roof', 'room', 'root', 'rope', 'rose',
        'rough', 'roughly', 'round', 'route', 'routine', 'royal', 'ruin', 'rule', 'ruler', 'rumor',
        'running', 'rural', 'rush', 'sacred', 'safe', 'safety', 'sake', 'salad', 'salary', 'sale',
        'sales', 'salt', 'same', 'sample', 'sanction', 'sand', 'satisfaction', 'satisfy', 'sauce', 'save',
        'saving', 'scale', 'scandal', 'scared', 'scenario', 'scene', 'schedule', 'scheme', 'scholar', 'scholarship',
        'school', 'science', 'scientific', 'scientist', 'scope', 'score', 'scream', 'screen', 'script', 'search',
        'season', 'seat', 'second', 'secret', 'secretary', 'section', 'sector', 'secure', 'security', 'seed',
        'seek', 'seem', 'segment', 'seize', 'select', 'selection', 'self', 'sell', 'senate', 'senator',
        'send', 'senior', 'sense', 'sensitive', 'sentence', 'separate', 'sequence', 'series', 'serious', 'seriously',
        'serve', 'service', 'session', 'setting', 'settle', 'settlement', 'seven', 'several', 'severe', 'sexual',
        'shade', 'shadow', 'shake', 'shall', 'shape', 'share', 'sharp', 'shatter', 'shed', 'sheep',
        'sheet', 'shelf', 'shell', 'shelter', 'shift', 'shine', 'ship', 'shirt', 'shock', 'shoe',
        'shoot', 'shooting', 'shop', 'shopping', 'shore', 'short', 'shortly', 'shot', 'should', 'shoulder',
        'shout', 'show', 'shower', 'shrug', 'shut', 'sick', 'side', 'sigh', 'sight', 'sign',
        'signal', 'significance', 'significant', 'significantly', 'silence', 'silent', 'silver', 'similar', 'similarly', 'simple',
        'simply', 'simulation', 'simultaneously', 'since', 'sing', 'singer', 'single', 'sink', 'sister', 'site',
        'situation', 'size', 'skill', 'skin', 'skip', 'skull', 'sleep', 'slice', 'slide', 'slight',
        'slightly', 'slip', 'slow', 'slowly', 'small', 'smart', 'smell', 'smile', 'smoke', 'smooth',
        'snap', 'snow', 'so', 'soap', 'soccer', 'social', 'society', 'soft', 'software', 'soil',
        'solar', 'soldier', 'solid', 'solution', 'solve', 'some', 'somebody', 'somehow', 'someone', 'something',
        'sometimes', 'somewhat', 'somewhere', 'song', 'soon', 'sophisticated', 'sorry', 'sort', 'soul', 'sound',
        'soup', 'source', 'south', 'southern', 'space', 'span', 'speak', 'speaker', 'special', 'specialist',
        'species', 'specific', 'specifically', 'speech', 'speed', 'spend', 'spending', 'spin', 'spirit', 'spiritual',
        'split', 'spokesman', 'sponsor', 'sport', 'spot', 'spread', 'spring', 'square', 'squeeze', 'stability',
        'stable', 'staff', 'stage', 'stair', 'stake', 'stand', 'standard', 'standing', 'star', 'stare',
        'start', 'state', 'statement', 'station', 'statistics', 'status', 'stay', 'steady', 'steal', 'steel',
        'steep', 'steer', 'stem', 'step', 'stick', 'still', 'stimulate', 'stir', 'stock', 'stomach',
        'stone', 'stop', 'storage', 'store', 'storm', 'story', 'straight', 'strange', 'stranger', 'strategic',
        'strategy', 'stream', 'street', 'strength', 'strengthen', 'stress', 'stretch', 'strike', 'string', 'strip',
        'stroke', 'strong', 'strongly', 'structure', 'struggle', 'student', 'studio', 'study', 'stuff', 'stupid',
        'style', 'subject', 'submit', 'subsequent', 'substance', 'substantial', 'succeed', 'success', 'successful', 'successfully',
        'such', 'sudden', 'suddenly', 'suffer', 'sufficient', 'sugar', 'suggest', 'suggestion', 'suicide', 'suit',
        'summer', 'summit', 'super', 'supply', 'support', 'supporter', 'suppose', 'supposed', 'supreme', 'sure',
        'surely', 'surface', 'surgery', 'surprise', 'surprised', 'surprising', 'surprisingly', 'surround', 'survey', 'survival',
        'survive', 'survivor', 'suspect', 'sustain', 'swear', 'sweep', 'sweet', 'swim', 'swing', 'switch',
        'symbol', 'symptom', 'system', 'table', 'tablespoon', 'tactic', 'tail', 'take', 'tale', 'talent',
        'talk', 'tall', 'tank', 'tape', 'target', 'task', 'taste', 'teach', 'teacher', 'teaching',
        'team', 'tear', 'teaspoon', 'technical', 'technique', 'technology', 'teen', 'teenager', 'telephone', 'telescope',
        'television', 'tell', 'temperature', 'temporary', 'tend', 'tendency', 'tennis', 'tension', 'tent', 'term',
        'terms', 'terrible', 'territory', 'terror', 'terrorism', 'terrorist', 'test', 'testify', 'testimony', 'testing',
        'text', 'than', 'thank', 'that', 'theater', 'their', 'them', 'theme', 'themselves', 'then',
        'theory', 'therapy', 'there', 'therefore', 'these', 'they', 'thick', 'thin', 'thing', 'think',
        'thinking', 'third', 'thirty', 'this', 'those', 'though', 'thought', 'thousand', 'threat', 'threaten',
        'three', 'throat', 'through', 'throughout', 'throw', 'thus', 'ticket', 'tide', 'tight', 'time',
        'tiny', 'tire', 'tired', 'tissue', 'title', 'tobacco', 'today', 'together', 'tomato', 'tomorrow',
        'tone', 'tongue', 'tonight', 'tool', 'tooth', 'topic', 'toss', 'total', 'totally', 'touch',
        'tough', 'tour', 'tourist', 'tournament', 'toward', 'towards', 'tower', 'town', 'trace', 'track',
        'trade', 'tradition', 'traditional', 'traffic', 'tragedy', 'trail', 'train', 'training', 'transfer', 'transform',
        'transformation', 'transition', 'translate', 'transmission', 'transport', 'transportation', 'trap', 'travel', 'treasure', 'treat',
        'treatment', 'treaty', 'tree', 'tremendous', 'trend', 'trial', 'tribe', 'trick', 'trip', 'troop',
        'trouble', 'truck', 'true', 'truly', 'trust', 'truth', 'tube', 'tunnel', 'turn', 'twelve',
        'twenty', 'twice', 'twin', 'type', 'typical', 'typically', 'ugly', 'ultimate', 'ultimately', 'unable',
        'uncle', 'under', 'undergo', 'understand', 'understanding', 'unemployment', 'unexpected', 'unfortunately', 'uniform', 'union',
        'unique', 'unit', 'unite', 'united', 'universal', 'universe', 'university', 'unknown', 'unless', 'unlike',
        'unlikely', 'until', 'unusual', 'upon', 'upper', 'urban', 'urge', 'usage', 'used', 'useful',
        'user', 'usual', 'usually', 'utility', 'vacation', 'valley', 'valuable', 'value', 'variable', 'variation',
        'variety', 'various', 'vary', 'vast', 'vegetable', 'vehicle', 'venture', 'version', 'versus', 'very',
        'vessel', 'veteran', 'veto', 'victim', 'victory', 'video', 'view', 'viewer', 'village', 'violate',
        'violation', 'violence', 'violent', 'virtual', 'virtually', 'virtue', 'virus', 'visible', 'vision', 'visit',
        'visitor', 'visual', 'vital', 'voice', 'volume', 'volunteer', 'vote', 'voter', 'wage', 'wait',
        'wake', 'walk', 'wall', 'wander', 'want', 'warfare', 'warm', 'warn', 'warning', 'wash',
        'waste', 'watch', 'water', 'wave', 'weak', 'wealth', 'wealthy', 'weapon', 'wear', 'weather',
        'wedding', 'week', 'weekend', 'weekly', 'weigh', 'weight', 'welcome', 'welfare', 'well', 'west',
        'western', 'what', 'whatever', 'wheat', 'wheel', 'when', 'whenever', 'where', 'whereas', 'whether',
        'which', 'while', 'whisper', 'white', 'whole', 'whom', 'whose', 'wide', 'widely', 'widespread',
        'wife', 'wild', 'will', 'willing', 'wind', 'window', 'wine', 'wing', 'winner', 'winter',
        'wipe', 'wire', 'wisdom', 'wise', 'wish', 'with', 'withdraw', 'within', 'without', 'witness',
        'woman', 'wonder', 'wonderful', 'wood', 'wooden', 'word', 'work', 'worker', 'working', 'works',
        'workshop', 'world', 'worried', 'worry', 'worth', 'would', 'wound', 'wrap', 'write', 'writer',
        'writing', 'wrong', 'yard', 'yeah', 'year', 'yell', 'yellow', 'yesterday', 'yield', 'young', 'necktie', 'tie', 'establishment', 'mess', 'reestablishment', 'reoccupation',
        'your', 'yours', 'yourself', 'youth', 'zone', 'teheran','iraq','tetris','emil','antidisestablishmentarianism','supercalifragilisticexpialidocious','hippopotomonstrosesquippedaliophobia','mitochondria','pneumoultramicroscopicsilicovolcanoconiosis','uzbekistan','azerbaijan','liechtenstein','kyrgyzstan','yugoslavia','transnistria','djibouti','bratislava','quebecois','zanzibar','chisinau','timbuktu','valparaíso','saskatchewan','honshu','kamchatka','ulaanbaatar','norrköping','escherichia','xenotransplantation','floccinaucinihilipilification','honorificabilitudinitatibus','thyroparathyroidectomized','electroencephalographically','counterdemonstration','uncharacteristically','incomprehensibilities','disproportionableness','circumlocution','sesquipedalian','otorhinolaryngological','spectrophotofluorometrically','psychoneuroendocrinological','hepaticocholangiocholecystenterostomies','laryngotracheobronchitis','pancreaticoduodenostomy','dichlorodifluoromethane','tetrahydrocannabinol','archaeopteryx','brachiosaurus','pachycephalosaurus','micropachycephalosaurus', 'tage', 'tymofii', 'oscar', 'omar', 'or', 'lore', 'ore', 'oar'
    ])
    words = list(set(list(common_words) + dwyl_words))
    return words

WORD_LIST = load_word_list()

# Замініть вашу поточну функцію generate_prompt на цю:
def generate_prompt():
    common_prompts = [
        "an", "in", "er", "re", "ed", "es", "on", "it", "or", "te",
        "at", "is", "he", "st", "nd", "nt", "en", "th", "de", "se",
        "mi", "be", "ve", "ne", "ti", "ro", "sh", "ch", "le", "al",
    ]
    return random.choice(common_prompts)


def is_valid_word(word, prompt):
    word = word.lower().strip()
    if len(word) < 3:
        return False
    if prompt.lower() not in word:
        return False
    return word in WORD_LIST

class Player:
    def __init__(self, player_id, username, session_id):
        self.player_id = player_id
        self.username = username
        self.session_id = session_id
        self.lives = INITIAL_LIVES
        self.status = 'active'
        self.score = 0

class GameRoom:
    def __init__(self, room_id, max_players=MAX_PLAYERS):
        self.room_id = room_id
        self.max_players = max_players
        self.players = []
        self.current_turn_index = 0
        self.current_prompt = None
        self.game_started = False
        self.used_words = set()
        self.timer_end_time = None
        self.game_over = False
        
    def add_player(self, player):
        if len(self.players) < self.max_players:
            self.players.append(player)
            return True
        return False
    
    def remove_player(self, player_id):
        self.players = [p for p in self.players if p.player_id != player_id]
        if len(self.players) < MIN_PLAYERS and self.game_started:
            self.game_started = False
            
    def get_active_players(self):
        return [p for p in self.players if p.status == 'active']
    
    def get_current_player(self):
        active_players = self.get_active_players()
        if not active_players:
            return None
        return active_players[self.current_turn_index % len(active_players)]
    
    def next_turn(self):
        active_players = self.get_active_players()
        if len(active_players) <= 1:
            self.game_over = True
            return None
        
        self.current_turn_index = (self.current_turn_index + 1) % len(active_players)
        self.current_prompt = generate_prompt()
        self.timer_end_time = time.time() + TURN_TIME
        return self.get_current_player()
    
    def start_game(self):
        if len(self.players) >= MIN_PLAYERS:
            self.game_started = True
            self.current_turn_index = 0
            self.current_prompt = generate_prompt()
            self.timer_end_time = time.time() + TURN_TIME
            self.used_words = set()
            for player in self.players:
                player.lives = INITIAL_LIVES
                player.status = 'active'
            return True
        return False
    
    def process_word(self, player_id, word):
        current_player = self.get_current_player()
        if not current_player or current_player.player_id != player_id:
            return {'success': False, 'message': 'Not your turn'}
        
        word_lower = word.lower().strip()
        if word_lower in self.used_words:
            return {'success': False, 'message': 'Word already used'}
        
        if not is_valid_word(word, self.current_prompt):
            return {'success': False, 'message': 'Invalid word'}
        
        self.used_words.add(word_lower)
        current_player.score += 1
        return {'success': True}
    
    def handle_bomb_explosion(self):
        current_player = self.get_current_player()
        if current_player:
            current_player.lives -= 1
            if current_player.lives <= 0:
                current_player.status = 'eliminated'
            return current_player
        return None
    
    def get_state(self):
        return {
            'room_id': self.room_id,
            'players': [{
                'player_id': p.player_id,
                'username': p.username,
                'lives': p.lives,
                'status': p.status,
                'score': p.score
            } for p in self.players],
            'current_turn': self.get_current_player().player_id if self.get_current_player() else None,
            'current_prompt': self.current_prompt,
            'game_started': self.game_started,
            'game_over': self.game_over,
            'time_remaining': max(0, int(self.timer_end_time - time.time())) if self.timer_end_time else 0
        }

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in players:
        player_info = players[sid]
        room_id = player_info['room_id']
        if room_id in rooms:
            rooms[room_id].remove_player(player_info['player_id'])
            socketio.emit('player_left', {
                'player_id': player_info['player_id'],
                'game_state': rooms[room_id].get_state()
            }, room=room_id)
            
            if len(rooms[room_id].players) == 0:
                if room_id in timers:
                    try:
                        timers[room_id].kill()
                    except:
                        pass
                    del timers[room_id]
                del rooms[room_id]
        del players[sid]
    print(f'Client disconnected: {sid}')

@socketio.on('create_room')
def handle_create_room(data):
    username = data.get('username', 'Player')
    room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    while room_id in rooms:
        room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    room = GameRoom(room_id)
    player_id = request.sid
    player = Player(player_id, username, request.sid)
    
    room.add_player(player)
    rooms[room_id] = room
    players[request.sid] = {'player_id': player_id, 'room_id': room_id}
    
    join_room(room_id)
    emit('room_created', {'room_id': room_id, 'game_state': room.get_state()})

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data.get('room_id')
    username = data.get('username', 'Player')
    
    if room_id not in rooms:
        emit('error', {'message': 'Room not found'})
        return
    
    room = rooms[room_id]
    if room.game_started:
        emit('error', {'message': 'Game already in progress'})
        return
    
    player_id = request.sid
    player = Player(player_id, username, request.sid)
    
    if room.add_player(player):
        players[request.sid] = {'player_id': player_id, 'room_id': room_id}
        join_room(room_id)
        emit('room_joined', {'game_state': room.get_state()})
        socketio.emit('player_joined', {'game_state': room.get_state()}, room=room_id)
    else:
        emit('error', {'message': 'Room is full'})

@socketio.on('start_game')
def handle_start_game():
    if request.sid not in players:
        return
    
    room_id = players[request.sid]['room_id']
    if room_id not in rooms:
        return
    
    room = rooms[room_id]
    if room.start_game():
        socketio.emit('game_started', {'game_state': room.get_state()}, room=room_id)
        start_timer(room_id)
    else:
        emit('error', {'message': f'Need at least {MIN_PLAYERS} players to start'})

@socketio.on('submit_word')
def handle_submit_word(data):
    if request.sid not in players:
        return
    
    word = data.get('word', '')
    player_id = players[request.sid]['player_id']
    room_id = players[request.sid]['room_id']
    
    if room_id not in rooms:
        return
    
    room = rooms[room_id]
    result = room.process_word(player_id, word)
    
    if result['success']:
        next_player = room.next_turn()
        socketio.emit('word_accepted', {
            'word': word,
            'player_id': player_id,
            'game_state': room.get_state()
        }, room=room_id)
        
        if timers.get(room_id):
            timers[room_id].kill()
        start_timer(room_id)
    else:
        emit('word_rejected', {'message': result['message']})

def start_timer(room_id):
    if room_id not in rooms:
        return
    
    room = rooms[room_id]
    if not room.game_started or room.game_over:
        return
    
    def timer_callback():
        for remaining in range(TURN_TIME, -1, -1):
            if room_id not in rooms:
                return
            
            current_room = rooms[room_id]
            if not current_room.game_started or current_room.game_over:
                return
            
            socketio.emit('timer_update', {'time_remaining': remaining}, room=room_id)
            
            if remaining == 0:
                exploded_player = current_room.handle_bomb_explosion()
                if exploded_player:
                    socketio.emit('bomb_exploded', {
                        'player_id': exploded_player.player_id,
                        'game_state': current_room.get_state()
                    }, room=room_id)
                
                active_players = current_room.get_active_players()
                if len(active_players) <= 1:
                    current_room.game_over = True
                    winner = active_players[0] if active_players else None
                    socketio.emit('game_over', {
                        'winner': {
                            'player_id': winner.player_id,
                            'username': winner.username,
                            'score': winner.score
                        } if winner else None,
                        'game_state': current_room.get_state()
                    }, room=room_id)
                    if room_id in timers:
                        del timers[room_id]
                    return
                
                current_room.next_turn()
                socketio.emit('next_turn', {'game_state': current_room.get_state()}, room=room_id)
                if room_id in timers:
                    del timers[room_id]
                start_timer(room_id)
                return
            
            eventlet.sleep(1)
    
    if room_id in timers:
        try:
            timers[room_id].kill()
        except:
            pass
    
    timer = eventlet.spawn(timer_callback)
    timers[room_id] = timer

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
