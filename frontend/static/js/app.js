/**
 * Smart Farming AI Agent — Frontend JS
 * Handles: Auth, Chat, Location, Weather, Full UI i18n
 */

const API = '/api/v1';
let isLoading = false;
let currentUser = null;
let currentLang = 'en';

// ── DOM refs ─────────────────────────────────────────────
const authPage      = document.getElementById('authPage');
const appPage       = document.getElementById('appPage');
const msgs          = document.getElementById('messagesContainer');
const qInput        = document.getElementById('questionInput');
const sendBtn       = document.getElementById('sendBtn');
const charCount     = document.getElementById('charCount');
const healthDot     = document.getElementById('healthDot');
const weatherWidget = document.getElementById('weatherWidget');
const weatherContent= document.getElementById('weatherContent');
const userNameDisplay=document.getElementById('userNameDisplay');
const profileLocation=document.getElementById('profileLocation');
const chatSubtitle  = document.getElementById('chatSubtitle');

// ══════════════════════════════════════════════════════════
// i18n TRANSLATIONS
// ══════════════════════════════════════════════════════════
const T = {
  en: {
    langLabel:       'Language / भाषा',
    locationLabel:   'Farm Location',
    locationSearch:  '🔍 Search city or district...',
    gpsBtn:          '📡 Auto-detect GPS',
    quickLabel:      'Quick Questions',
    weatherLabel:    '🌤️ Current Weather',
    chatTitle:       'Farming Assistant',
    chatSubtitle:    'Ask about crops, weather, pests, market prices & more',
    placeholder:     "Type your question... e.g. 'What crop to sow in winter?'",
    sendBtn:         'Send',
    sendingBtn:      'Asking…',
    clearBtn:        '🗑️ Clear',
    charHint:        'Ctrl+Enter to send',
    logoutBtn:       'Logout',
    greeting:        (name) => `Welcome back, ${name}! 👋 How can I help with your farm today?`,
    thinkingMsg:     'IBM Granite is thinking…',
    confidence:      'Confidence',
    sources:         'Sources',
    quick: [
      { label: '🌾 Best Kharif crop?',     q: 'What crop should I grow this Kharif season?' },
      { label: '💰 Tomato mandi price?',   q: "What is today's mandi rate for tomatoes?" },
      { label: '🐛 Wheat pest control?',   q: 'How to control pests in wheat crop organically?' },
      { label: '💧 Rice irrigation?',      q: 'When should I irrigate my rice crop?' },
      { label: '🌱 Improve soil health?',  q: 'How to improve soil health naturally?' },
      { label: '🏛️ Govt schemes?',         q: 'What government schemes are available for small farmers?' },
      { label: '📋 Wheat MSP 2024-25?',    q: 'What is the MSP for wheat this year 2024-25?' },
      { label: '🍅 Tomato leaf curl?',     q: 'My tomato leaves are curling, what disease is this?' },
    ],
    catLabels: { crop:'Crop Advice', weather:'Weather', pest:'Pest Control', soil:'Soil & Fertilizer', market:'Market Prices', general:'General' },
    weatherRain: 'Rain', weatherWind: 'Wind', weatherHumidity: 'Humidity',
    locRegistered: (loc) => `📍 Registered location: ${loc}`,
  },
  hi: {
    langLabel:       'भाषा / Language',
    locationLabel:   'खेत का स्थान',
    locationSearch:  '🔍 शहर या जिला खोजें...',
    gpsBtn:          '📡 GPS से पता लगाएं',
    quickLabel:      'त्वरित प्रश्न',
    weatherLabel:    '🌤️ वर्तमान मौसम',
    chatTitle:       'कृषि सहायक',
    chatSubtitle:    'फसल, मौसम, कीट, बाजार भाव और अधिक पूछें',
    placeholder:     "अपना प्रश्न लिखें... जैसे 'मेरी फसल में कीड़े लग रहे हैं क्या करूँ?'",
    sendBtn:         'भेजें',
    sendingBtn:      'पूछ रहे हैं…',
    clearBtn:        '🗑️ साफ करें',
    charHint:        'भेजने के लिए Ctrl+Enter दबाएं',
    logoutBtn:       'लॉग आउट',
    greeting:        (name) => `वापस आपका स्वागत है, ${name}! 👋 आज आपके खेत के लिए कैसे मदद करूँ?`,
    thinkingMsg:     'IBM Granite सोच रहा है…',
    confidence:      'विश्वसनीयता',
    sources:         'स्रोत',
    quick: [
      { label: '🌾 खरीफ की सबसे अच्छी फसल?',  q: 'इस खरीफ सीज़न में कौन सी फसल उगाऊं?' },
      { label: '💰 टमाटर का मंडी भाव?',          q: 'आज टमाटर का मंडी भाव क्या है?' },
      { label: '🐛 गेहूं में कीट नियंत्रण?',     q: 'गेहूं की फसल में जैविक तरीके से कीट कैसे नियंत्रित करें?' },
      { label: '💧 धान की सिंचाई?',              q: 'मेरी धान की फसल में कब सिंचाई करनी चाहिए?' },
      { label: '🌱 मिट्टी स्वास्थ्य सुधार?',     q: 'मिट्टी की सेहत प्राकृतिक रूप से कैसे सुधारें?' },
      { label: '🏛️ सरकारी योजनाएं?',             q: 'छोटे किसानों के लिए कौन सी सरकारी योजनाएं हैं?' },
      { label: '📋 गेहूं MSP 2024-25?',           q: 'इस साल 2024-25 में गेहूं का MSP क्या है?' },
      { label: '🍅 टमाटर पत्ती मुड़ना?',          q: 'मेरे टमाटर की पत्तियां मुड़ रही हैं, यह कौन सी बीमारी है?' },
    ],
    catLabels: { crop:'फसल सलाह', weather:'मौसम', pest:'कीट नियंत्रण', soil:'मिट्टी और उर्वरक', market:'बाजार भाव', general:'सामान्य' },
    weatherRain: 'वर्षा', weatherWind: 'हवा', weatherHumidity: 'नमी',
    locRegistered: (loc) => `📍 पंजीकृत स्थान: ${loc}`,
  },
  mr: {
    langLabel:       'भाषा / Language',
    locationLabel:   'शेताचे ठिकाण',
    locationSearch:  '🔍 शहर किंवा जिल्हा शोधा...',
    gpsBtn:          '📡 GPS ने शोधा',
    quickLabel:      'त्वरित प्रश्न',
    weatherLabel:    '🌤️ सध्याचे हवामान',
    chatTitle:       'शेती सहाय्यक',
    chatSubtitle:    'पीक, हवामान, कीड, बाजारभाव आणि अधिक विचारा',
    placeholder:     "तुमचा प्रश्न लिहा... उदा. 'खरीप हंगामात कोणते पीक घ्यावे?'",
    sendBtn:         'पाठवा',
    sendingBtn:      'विचारत आहे…',
    clearBtn:        '🗑️ साफ करा',
    charHint:        'पाठवण्यासाठी Ctrl+Enter दाबा',
    logoutBtn:       'लॉग आउट',
    greeting:        (name) => `पुन्हा स्वागत आहे, ${name}! 👋 आज तुमच्या शेतासाठी कशी मदत करू?`,
    thinkingMsg:     'IBM Granite विचार करत आहे…',
    confidence:      'विश्वासार्हता',
    sources:         'स्रोत',
    quick: [
      { label: '🌾 खरीपातील सर्वोत्तम पीक?',   q: 'या खरीप हंगामात कोणते पीक घ्यावे?' },
      { label: '💰 टोमॅटो बाजारभाव?',           q: 'आजचा टोमॅटोचा बाजारभाव काय आहे?' },
      { label: '🐛 गहू कीड नियंत्रण?',          q: 'गहू पिकातील कीड सेंद्रिय पद्धतीने कशी नियंत्रित करावी?' },
      { label: '💧 भात सिंचन?',                  q: 'माझ्या भात पिकाला कधी पाणी द्यावे?' },
      { label: '🌱 जमीन सुधारणा?',               q: 'जमिनीचे आरोग्य नैसर्गिकरित्या कसे सुधारावे?' },
      { label: '🏛️ सरकारी योजना?',              q: 'छोट्या शेतकऱ्यांसाठी कोणत्या सरकारी योजना आहेत?' },
      { label: '📋 गहू MSP 2024-25?',            q: 'या वर्षी 2024-25 मध्ये गव्हाचा MSP किती आहे?' },
      { label: '🍅 टोमॅटो पान कुरळे?',           q: 'माझ्या टोमॅटोची पाने कुरळी होत आहेत, हा कोणता रोग आहे?' },
    ],
    catLabels: { crop:'पीक सल्ला', weather:'हवामान', pest:'कीड नियंत्रण', soil:'माती आणि खत', market:'बाजारभाव', general:'सामान्य' },
    weatherRain: 'पाऊस', weatherWind: 'वारा', weatherHumidity: 'आर्द्रता',
    locRegistered: (loc) => `📍 नोंदणीकृत ठिकाण: ${loc}`,
  },
  te: {
    langLabel:       'భాష / Language',
    locationLabel:   'పొలం స్థానం',
    locationSearch:  '🔍 నగరం లేదా జిల్లా శోధించండి...',
    gpsBtn:          '📡 GPS ద్వారా గుర్తించండి',
    quickLabel:      'త్వరిత ప్రశ్నలు',
    weatherLabel:    '🌤️ ప్రస్తుత వాతావరణం',
    chatTitle:       'వ్యవసాయ సహాయకుడు',
    chatSubtitle:    'పంటలు, వాతావరణం, చీడలు, మార్కెట్ ధరలు గురించి అడగండి',
    placeholder:     "మీ ప్రశ్న టైప్ చేయండి... ఉదా. 'ఈ సీజన్‌లో ఏ పంట పండించాలి?'",
    sendBtn:         'పంపించు',
    sendingBtn:      'అడుగుతున్నాం…',
    clearBtn:        '🗑️ క్లియర్',
    charHint:        'పంపడానికి Ctrl+Enter నొక్కండి',
    logoutBtn:       'లాగ్ అవుట్',
    greeting:        (name) => `తిరిగి స్వాగతం, ${name}! 👋 ఈరోజు మీ పొలానికి ఎలా సహాయం చేయాలి?`,
    thinkingMsg:     'IBM Granite ఆలోచిస్తోంది…',
    confidence:      'విశ్వసనీయత',
    sources:         'మూలాలు',
    quick: [
      { label: '🌾 ఖరీఫ్ లో మంచి పంట?',       q: 'ఈ ఖరీఫ్ సీజన్‌లో ఏ పంట పండించాలి?' },
      { label: '💰 టమాటో మండి ధర?',             q: 'ఈరోజు టమాటో మండి ధర ఎంత?' },
      { label: '🐛 గోధుమ చీడ నివారణ?',          q: 'గోధుమ పంటలో చీడను సేంద్రీయంగా నియంత్రించడం ఎలా?' },
      { label: '💧 వరి నీటి పారుదల?',            q: 'నా వరి పంటకు ఎప్పుడు నీరు పోయాలి?' },
      { label: '🌱 నేల ఆరోగ్యం మెరుగుపరచడం?',  q: 'నేల ఆరోగ్యాన్ని సహజంగా మెరుగుపరచడం ఎలా?' },
      { label: '🏛️ ప్రభుత్వ పథకాలు?',           q: 'చిన్న రైతులకు ఏ ప్రభుత్వ పథకాలు అందుబాటులో ఉన్నాయి?' },
      { label: '📋 గోధుమ MSP 2024-25?',          q: 'ఈ సంవత్సరం 2024-25లో గోధుమ MSP ఎంత?' },
      { label: '🍅 టమాటో ఆకు ముడత?',            q: 'నా టమాటో ఆకులు ముడుచుకుంటున్నాయి, ఏ వ్యాధి?' },
    ],
    catLabels: { crop:'పంట సలహా', weather:'వాతావరణం', pest:'చీడ నివారణ', soil:'నేల & ఎరువు', market:'మార్కెట్ ధరలు', general:'సాధారణ' },
    weatherRain: 'వర్షం', weatherWind: 'గాలి', weatherHumidity: 'తేమ',
    locRegistered: (loc) => `📍 నమోదు స్థానం: ${loc}`,
  },
  ta: {
    langLabel:       'மொழி / Language',
    locationLabel:   'பண்ணை இடம்',
    locationSearch:  '🔍 நகரம் அல்லது மாவட்டம் தேடுக...',
    gpsBtn:          '📡 GPS மூலம் கண்டறி',
    quickLabel:      'விரைவு கேள்விகள்',
    weatherLabel:    '🌤️ தற்போதைய வானிலை',
    chatTitle:       'விவசாய உதவியாளர்',
    chatSubtitle:    'பயிர்கள், வானிலை, பூச்சிகள், சந்தை விலைகள் பற்றி கேளுங்கள்',
    placeholder:     "உங்கள் கேள்வியை தட்டச்சு செய்யுங்கள்... எ.கா. 'இந்த பருவத்தில் எந்த பயிர் பயிரிடலாம்?'",
    sendBtn:         'அனுப்பு',
    sendingBtn:      'கேட்கிறோம்…',
    clearBtn:        '🗑️ அழி',
    charHint:        'அனுப்ப Ctrl+Enter அழுத்துங்கள்',
    logoutBtn:       'வெளியேறு',
    greeting:        (name) => `மீண்டும் வரவேற்கிறோம், ${name}! 👋 இன்று உங்கள் பண்ணைக்கு எப்படி உதவலாம்?`,
    thinkingMsg:     'IBM Granite யோசிக்கிறது…',
    confidence:      'நம்பகத்தன்மை',
    sources:         'ஆதாரங்கள்',
    quick: [
      { label: '🌾 சிறந்த கரீஃப் பயிர்?',     q: 'இந்த கரீஃப் பருவத்தில் எந்த பயிர் பயிரிட வேண்டும்?' },
      { label: '💰 தக்காளி மண்டி விலை?',       q: 'இன்று தக்காளியின் மண்டி விலை என்ன?' },
      { label: '🐛 கோதுமை பூச்சி கட்டுப்பாடு?', q: 'கோதுமை பயிரில் பூச்சிகளை இயற்கையாக கட்டுப்படுத்துவது எப்படி?' },
      { label: '💧 நெல் நீர்ப்பாசனம்?',         q: 'என் நெல் பயிருக்கு எப்போது நீர் பாய்ச்ச வேண்டும்?' },
      { label: '🌱 மண் ஆரோக்கியம் மேம்பாடு?', q: 'மண்ணின் ஆரோக்கியத்தை இயற்கையாக எப்படி மேம்படுத்துவது?' },
      { label: '🏛️ அரசு திட்டங்கள்?',          q: 'சிறு விவசாயிகளுக்கு என்ன அரசு திட்டங்கள் உள்ளன?' },
      { label: '📋 கோதுமை MSP 2024-25?',        q: 'இந்த ஆண்டு 2024-25ல் கோதுமை MSP என்ன?' },
      { label: '🍅 தக்காளி இலை சுருட்டு?',     q: 'என் தக்காளி இலைகள் சுருண்டு போகின்றன, இது என்ன நோய்?' },
    ],
    catLabels: { crop:'பயிர் ஆலோசனை', weather:'வானிலை', pest:'பூச்சி கட்டுப்பாடு', soil:'மண் & உரம்', market:'சந்தை விலைகள்', general:'பொது' },
    weatherRain: 'மழை', weatherWind: 'காற்று', weatherHumidity: 'ஈரப்பதம்',
    locRegistered: (loc) => `📍 பதிவு செய்யப்பட்ட இடம்: ${loc}`,
  },
  kn: {
    langLabel:       'ಭಾಷೆ / Language',
    locationLabel:   'ತೋಟದ ಸ್ಥಳ',
    locationSearch:  '🔍 ನಗರ ಅಥವಾ ಜಿಲ್ಲೆ ಹುಡುಕಿ...',
    gpsBtn:          '📡 GPS ಮೂಲಕ ಪತ್ತೆ ಮಾಡಿ',
    quickLabel:      'ತ್ವರಿತ ಪ್ರಶ್ನೆಗಳು',
    weatherLabel:    '🌤️ ಪ್ರಸ್ತುತ ಹವಾಮಾನ',
    chatTitle:       'ಕೃಷಿ ಸಹಾಯಕ',
    chatSubtitle:    'ಬೆಳೆ, ಹವಾಮಾನ, ಕೀಟ, ಮಾರುಕಟ್ಟೆ ಬೆಲೆ ಬಗ್ಗೆ ಕೇಳಿ',
    placeholder:     "ನಿಮ್ಮ ಪ್ರಶ್ನೆ ಟೈಪ್ ಮಾಡಿ... ಉದಾ. 'ಈ ಋತುವಿನಲ್ಲಿ ಯಾವ ಬೆಳೆ ಬೆಳೆಯಬೇಕು?'",
    sendBtn:         'ಕಳಿಸಿ',
    sendingBtn:      'ಕೇಳುತ್ತಿದ್ದೇವೆ…',
    clearBtn:        '🗑️ ತೆರವು',
    charHint:        'ಕಳಿಸಲು Ctrl+Enter ಒತ್ತಿ',
    logoutBtn:       'ಲಾಗ್ ಔಟ್',
    greeting:        (name) => `ಮತ್ತೆ ಸ್ವಾಗತ, ${name}! 👋 ಇಂದು ನಿಮ್ಮ ತೋಟಕ್ಕೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?`,
    thinkingMsg:     'IBM Granite ಯೋಚಿಸುತ್ತಿದೆ…',
    confidence:      'ವಿಶ್ವಾಸಾರ್ಹತೆ',
    sources:         'ಮೂಲಗಳು',
    quick: [
      { label: '🌾 ಖರೀಫ್‌ನಲ್ಲಿ ಉತ್ತಮ ಬೆಳೆ?',   q: 'ಈ ಖರೀಫ್ ಋತುವಿನಲ್ಲಿ ಯಾವ ಬೆಳೆ ಬೆಳೆಯಬೇಕು?' },
      { label: '💰 ಟೊಮ್ಯಾಟೊ ಮಂಡಿ ಬೆಲೆ?',        q: 'ಇಂದು ಟೊಮ್ಯಾಟೊ ಮಂಡಿ ಬೆಲೆ ಎಷ್ಟು?' },
      { label: '🐛 ಗೋಧಿ ಕೀಟ ನಿಯಂತ್ರಣ?',         q: 'ಗೋಧಿ ಬೆಳೆಯಲ್ಲಿ ಕೀಟವನ್ನು ಸಾವಯವ ಪದ್ಧತಿಯಲ್ಲಿ ನಿಯಂತ್ರಿಸುವುದು ಹೇಗೆ?' },
      { label: '💧 ಭತ್ತದ ನೀರಾವರಿ?',              q: 'ನನ್ನ ಭತ್ತದ ಬೆಳೆಗೆ ಯಾವಾಗ ನೀರು ಹಾಕಬೇಕು?' },
      { label: '🌱 ಮಣ್ಣಿನ ಆರೋಗ್ಯ ಸುಧಾರಣೆ?',    q: 'ಮಣ್ಣಿನ ಆರೋಗ್ಯವನ್ನು ನೈಸರ್ಗಿಕವಾಗಿ ಸುಧಾರಿಸುವುದು ಹೇಗೆ?' },
      { label: '🏛️ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು?',         q: 'ಸಣ್ಣ ರೈತರಿಗೆ ಯಾವ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳಿವೆ?' },
      { label: '📋 ಗೋಧಿ MSP 2024-25?',           q: 'ಈ ವರ್ಷ 2024-25 ರಲ್ಲಿ ಗೋಧಿ MSP ಎಷ್ಟು?' },
      { label: '🍅 ಟೊಮ್ಯಾಟೊ ಎಲೆ ಸುರುಳಿ?',       q: 'ನನ್ನ ಟೊಮ್ಯಾಟೊ ಎಲೆಗಳು ಸುರುಳಿಯಾಗುತ್ತಿವೆ, ಯಾವ ರೋಗ?' },
    ],
    catLabels: { crop:'ಬೆಳೆ ಸಲಹೆ', weather:'ಹವಾಮಾನ', pest:'ಕೀಟ ನಿಯಂತ್ರಣ', soil:'ಮಣ್ಣು & ಗೊಬ್ಬರ', market:'ಮಾರುಕಟ್ಟೆ ಬೆಲೆ', general:'ಸಾಮಾನ್ಯ' },
    weatherRain: 'ಮಳೆ', weatherWind: 'ಗಾಳಿ', weatherHumidity: 'ತೇವಾಂಶ',
    locRegistered: (loc) => `📍 ನೋಂದಾಯಿಸಿದ ಸ್ಥಳ: ${loc}`,
  },
  gu: {
    langLabel:       'ભાષા / Language',
    locationLabel:   'ખેતરનું સ્થળ',
    locationSearch:  '🔍 શહેર અથવા જિલ્લો શોધો...',
    gpsBtn:          '📡 GPS થી શોધો',
    quickLabel:      'ઝડપી પ્રશ્નો',
    weatherLabel:    '🌤️ હાલનું હવામાન',
    chatTitle:       'કૃષિ સહાયક',
    chatSubtitle:    'પાક, હવામાન, જીવાત, બજાર ભાવ વિશે પૂછો',
    placeholder:     "તમારો પ્રશ્ન ટાઈપ કરો... ઉદા. 'ખરીફ સિઝનમાં કયો પાક ઉગાડવો?'",
    sendBtn:         'મોકલો',
    sendingBtn:      'પૂછી રહ્યા છીએ…',
    clearBtn:        '🗑️ સાફ કરો',
    charHint:        'મોકલવા Ctrl+Enter દબાવો',
    logoutBtn:       'લૉગ આઉટ',
    greeting:        (name) => `પાછા આવ્યા, ${name}! 👋 આજે તમારા ખેતર માટે કેવી મદદ કરું?`,
    thinkingMsg:     'IBM Granite વિચારી રહ્યો છે…',
    confidence:      'વિશ્વસનીયતા',
    sources:         'સ્રોત',
    quick: [
      { label: '🌾 ખરીફ સૌથી સારો પાક?',      q: 'આ ખરીફ સિઝનમાં કયો પાક ઉગાડવો?' },
      { label: '💰 ટામેટાનો મંડી ભાવ?',          q: 'આજે ટામેટાનો મંડી ભાવ શું છે?' },
      { label: '🐛 ઘઉં જીવાત નિયંત્રણ?',         q: 'ઘઉંના પાકમાં જૈવિક રીતે જીવાત કેવી રીતે નિયંત્રિત કરવી?' },
      { label: '💧 ડાંગર સિંચાઈ?',               q: 'મારા ડાંગરના પાકને ક્યારે પાણી આપવું?' },
      { label: '🌱 જમીનનું સ્વાસ્થ્ય સુધારો?',  q: 'જમીનનું સ્વાસ્થ્ય કુદરતી રીતે કેવી રીતે સુધારવું?' },
      { label: '🏛️ સરકારી યોજનાઓ?',             q: 'નાના ખેડૂતો માટે કઈ સરકારી યોજનાઓ છે?' },
      { label: '📋 ઘઉં MSP 2024-25?',            q: 'આ વર્ષ 2024-25 માં ઘઉંનો MSP કેટલો છે?' },
      { label: '🍅 ટામેટાની પાન કોકડું?',         q: 'મારા ટામેટાના પાન વળી રહ્યા છે, આ કઈ બીમારી છે?' },
    ],
    catLabels: { crop:'પાક સલાહ', weather:'હવામાન', pest:'જીવાત નિયંત્રણ', soil:'જમીન & ખાતર', market:'બજાર ભાવ', general:'સામાન્ય' },
    weatherRain: 'વરસાદ', weatherWind: 'પવન', weatherHumidity: 'ભેજ',
    locRegistered: (loc) => `📍 નોંધાયેલ સ્થળ: ${loc}`,
  },
  pa: {
    langLabel:       'ਭਾਸ਼ਾ / Language',
    locationLabel:   'ਖੇਤ ਦੀ ਜਗ੍ਹਾ',
    locationSearch:  '🔍 ਸ਼ਹਿਰ ਜਾਂ ਜ਼ਿਲ੍ਹਾ ਖੋਜੋ...',
    gpsBtn:          '📡 GPS ਨਾਲ ਪਤਾ ਲਗਾਓ',
    quickLabel:      'ਤੇਜ਼ ਸਵਾਲ',
    weatherLabel:    '🌤️ ਮੌਜੂਦਾ ਮੌਸਮ',
    chatTitle:       'ਖੇਤੀ ਸਹਾਇਕ',
    chatSubtitle:    'ਫ਼ਸਲ, ਮੌਸਮ, ਕੀੜੇ, ਮੰਡੀ ਭਾਅ ਬਾਰੇ ਪੁੱਛੋ',
    placeholder:     "ਆਪਣਾ ਸਵਾਲ ਲਿਖੋ... ਜਿਵੇਂ 'ਇਸ ਖਰੀਫ਼ ਵਿੱਚ ਕਿਹੜੀ ਫ਼ਸਲ ਬੀਜਾਂ?'",
    sendBtn:         'ਭੇਜੋ',
    sendingBtn:      'ਪੁੱਛ ਰਹੇ ਹਾਂ…',
    clearBtn:        '🗑️ ਸਾਫ਼ ਕਰੋ',
    charHint:        'ਭੇਜਣ ਲਈ Ctrl+Enter ਦਬਾਓ',
    logoutBtn:       'ਲੌਗ ਆਊਟ',
    greeting:        (name) => `ਵਾਪਸ ਜੀ ਆਇਆਂ, ${name}! 👋 ਅੱਜ ਤੁਹਾਡੇ ਖੇਤ ਲਈ ਕਿਵੇਂ ਮਦਦ ਕਰਾਂ?`,
    thinkingMsg:     'IBM Granite ਸੋਚ ਰਿਹਾ ਹੈ…',
    confidence:      'ਭਰੋਸੇਯੋਗਤਾ',
    sources:         'ਸਰੋਤ',
    quick: [
      { label: '🌾 ਖਰੀਫ਼ ਵਿੱਚ ਸਭ ਤੋਂ ਵਧੀਆ ਫ਼ਸਲ?', q: 'ਇਸ ਖਰੀਫ਼ ਸੀਜ਼ਨ ਵਿੱਚ ਕਿਹੜੀ ਫ਼ਸਲ ਬੀਜਾਂ?' },
      { label: '💰 ਟਮਾਟਰ ਮੰਡੀ ਭਾਅ?',              q: 'ਅੱਜ ਟਮਾਟਰ ਦਾ ਮੰਡੀ ਭਾਅ ਕੀ ਹੈ?' },
      { label: '🐛 ਕਣਕ ਕੀੜਾ ਕੰਟਰੋਲ?',             q: 'ਕਣਕ ਦੀ ਫ਼ਸਲ ਵਿੱਚ ਕੀੜੇ ਜੈਵਿਕ ਤਰੀਕੇ ਨਾਲ ਕਿਵੇਂ ਕੰਟਰੋਲ ਕਰੀਏ?' },
      { label: '💧 ਝੋਨੇ ਦੀ ਸਿੰਚਾਈ?',               q: 'ਮੇਰੇ ਝੋਨੇ ਦੀ ਫ਼ਸਲ ਨੂੰ ਕਦੋਂ ਪਾਣੀ ਦੇਣਾ ਚਾਹੀਦਾ ਹੈ?' },
      { label: '🌱 ਜ਼ਮੀਨ ਸਿਹਤ ਸੁਧਾਰ?',            q: 'ਜ਼ਮੀਨ ਦੀ ਸਿਹਤ ਕੁਦਰਤੀ ਤਰੀਕੇ ਨਾਲ ਕਿਵੇਂ ਸੁਧਾਰੀਏ?' },
      { label: '🏛️ ਸਰਕਾਰੀ ਸਕੀਮਾਂ?',               q: 'ਛੋਟੇ ਕਿਸਾਨਾਂ ਲਈ ਕਿਹੜੀਆਂ ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਹਨ?' },
      { label: '📋 ਕਣਕ MSP 2024-25?',             q: 'ਇਸ ਸਾਲ 2024-25 ਵਿੱਚ ਕਣਕ ਦਾ MSP ਕੀ ਹੈ?' },
      { label: '🍅 ਟਮਾਟਰ ਪੱਤਾ ਮੁੜਨਾ?',            q: 'ਮੇਰੇ ਟਮਾਟਰ ਦੇ ਪੱਤੇ ਮੁੜ ਰਹੇ ਹਨ, ਇਹ ਕਿਹੜੀ ਬਿਮਾਰੀ ਹੈ?' },
    ],
    catLabels: { crop:'ਫ਼ਸਲ ਸਲਾਹ', weather:'ਮੌਸਮ', pest:'ਕੀੜਾ ਕੰਟਰੋਲ', soil:'ਮਿੱਟੀ & ਖਾਦ', market:'ਮੰਡੀ ਭਾਅ', general:'ਆਮ' },
    weatherRain: 'ਬਾਰਿਸ਼', weatherWind: 'ਹਵਾ', weatherHumidity: 'ਨਮੀ',
    locRegistered: (loc) => `📍 ਦਰਜ ਕੀਤਾ ਸਥਾਨ: ${loc}`,
  },
  bn: {
    langLabel:       'ভাষা / Language',
    locationLabel:   'খামারের অবস্থান',
    locationSearch:  '🔍 শহর বা জেলা খুঁজুন...',
    gpsBtn:          '📡 GPS দিয়ে সনাক্ত করুন',
    quickLabel:      'দ্রুত প্রশ্ন',
    weatherLabel:    '🌤️ বর্তমান আবহাওয়া',
    chatTitle:       'কৃষি সহকারী',
    chatSubtitle:    'ফসল, আবহাওয়া, পোকা, বাজার দর সম্পর্কে জিজ্ঞেস করুন',
    placeholder:     "আপনার প্রশ্ন লিখুন... যেমন 'খরিফ মৌসুমে কোন ফসল চাষ করব?'",
    sendBtn:         'পাঠান',
    sendingBtn:      'জিজ্ঞেস করছি…',
    clearBtn:        '🗑️ মুছুন',
    charHint:        'পাঠাতে Ctrl+Enter চাপুন',
    logoutBtn:       'লগ আউট',
    greeting:        (name) => `আবার স্বাগতম, ${name}! 👋 আজ আপনার খামারের জন্য কীভাবে সাহায্য করব?`,
    thinkingMsg:     'IBM Granite ভাবছে…',
    confidence:      'আস্থা',
    sources:         'উৎস',
    quick: [
      { label: '🌾 খরিফের সেরা ফসল?',         q: 'এই খরিফ মৌসুমে কোন ফসল চাষ করব?' },
      { label: '💰 টমেটোর মান্ডি দর?',          q: 'আজকের টমেটোর মান্ডি দর কত?' },
      { label: '🐛 গমে পোকা নিয়ন্ত্রণ?',       q: 'গম ফসলে জৈব পদ্ধতিতে পোকা কীভাবে নিয়ন্ত্রণ করব?' },
      { label: '💧 ধানে সেচ?',                  q: 'আমার ধান ফসলে কখন সেচ দেব?' },
      { label: '🌱 মাটির স্বাস্থ্য উন্নতি?',   q: 'প্রাকৃতিকভাবে মাটির স্বাস্থ্য কীভাবে উন্নত করব?' },
      { label: '🏛️ সরকারি প্রকল্প?',            q: 'ছোট কৃষকদের জন্য কোন সরকারি প্রকল্প আছে?' },
      { label: '📋 গম MSP 2024-25?',            q: 'এই বছর 2024-25 এ গমের MSP কত?' },
      { label: '🍅 টমেটো পাতা কুঁকড়ানো?',      q: 'আমার টমেটোর পাতা কুঁকড়ে যাচ্ছে, এটা কোন রোগ?' },
    ],
    catLabels: { crop:'ফসল পরামর্শ', weather:'আবহাওয়া', pest:'পোকা নিয়ন্ত্রণ', soil:'মাটি ও সার', market:'বাজার দর', general:'সাধারণ' },
    weatherRain: 'বৃষ্টি', weatherWind: 'বাতাস', weatherHumidity: 'আর্দ্রতা',
    locRegistered: (loc) => `📍 নিবন্ধিত অবস্থান: ${loc}`,
  },
  or: {
    langLabel:       'ଭାଷା / Language',
    locationLabel:   'ଜମି ସ୍ଥାନ',
    locationSearch:  '🔍 ସହର ବା ଜିଲ୍ଲା ଖୋଜନ୍ତୁ...',
    gpsBtn:          '📡 GPS ଦ୍ୱାରା ଚିହ୍ନଟ କରନ୍ତୁ',
    quickLabel:      'ଶୀଘ୍ର ପ୍ରଶ୍ନ',
    weatherLabel:    '🌤️ ବର୍ତ୍ତମାନ ପାଣିପାଗ',
    chatTitle:       'କୃଷି ସହାୟକ',
    chatSubtitle:    'ଫସଲ, ପାଣିପାଗ, ପୋକ, ବଜାର ଦର ବିଷୟରେ ପଚାରନ୍ତୁ',
    placeholder:     "ଆପଣଙ୍କ ପ୍ରଶ୍ନ ଲିଖନ୍ତୁ... ଯଥା 'ଖରିଫ ଋତୁରେ କେଉଁ ଫସଲ ଚାଷ କରିବି?'",
    sendBtn:         'ପଠାନ୍ତୁ',
    sendingBtn:      'ପଚାରୁଛୁ…',
    clearBtn:        '🗑️ ସଫା କରନ୍ତୁ',
    charHint:        'ପଠାଇବାକୁ Ctrl+Enter ଦବାନ୍ତୁ',
    logoutBtn:       'ଲଗ୍ ଆଉଟ',
    greeting:        (name) => `ପୁଣି ସ୍ୱାଗତ, ${name}! 👋 ଆଜି ଆପଣଙ୍କ ଜମି ପାଇଁ କିପରି ସାହାଯ୍ୟ କରିବି?`,
    thinkingMsg:     'IBM Granite ଭାବୁଛି…',
    confidence:      'ବିଶ୍ୱାସଯୋଗ୍ୟତା',
    sources:         'ଉତ୍ସ',
    quick: [
      { label: '🌾 ଖରିଫରେ ଭଲ ଫସଲ?',           q: 'ଏହି ଖରିଫ ଋତୁରେ କେଉଁ ଫସଲ ଚାଷ କରିବି?' },
      { label: '💰 ଟମାଟୋ ମଣ୍ଡି ଦର?',            q: 'ଆଜି ଟମାଟୋର ମଣ୍ଡି ଦର କେତେ?' },
      { label: '🐛 ଗହମ ପୋକ ନିୟନ୍ତ୍ରଣ?',         q: 'ଗହମ ଫସଲରେ ଜୈବ ପଦ୍ଧତିରେ ପୋକ କିପରି ନିୟନ୍ତ୍ରଣ କରିବି?' },
      { label: '💧 ଧାନ ଜଳସେଚନ?',               q: 'ମୋ ଧାନ ଫସଲକୁ କେବେ ପାଣି ଦେବି?' },
      { label: '🌱 ମାଟି ସ୍ୱାସ୍ଥ୍ୟ ଉନ୍ନତି?',    q: 'ମାଟିର ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରାକୃତିକ ଭାବରେ କିପରି ଉନ୍ନତ କରିବି?' },
      { label: '🏛️ ସରକାରୀ ଯୋଜନା?',             q: 'ଛୋଟ ଚାଷୀଙ୍କ ପାଇଁ କେଉଁ ସରକାରୀ ଯୋଜନା ଅଛି?' },
      { label: '📋 ଗହମ MSP 2024-25?',           q: 'ଏହି ବର୍ଷ 2024-25 ରେ ଗହମ MSP କେତେ?' },
      { label: '🍅 ଟମାଟୋ ପତ୍ର କୁଣ୍ଡଳ?',         q: 'ମୋ ଟମାଟୋ ପତ୍ର କୁଣ୍ଡଳ ହେଉଛି, ଏହା କେଉଁ ରୋଗ?' },
    ],
    catLabels: { crop:'ଫସଲ ପରାମର୍ଶ', weather:'ପାଣିପାଗ', pest:'ପୋକ ନିୟନ୍ତ୍ରଣ', soil:'ମାଟି ଓ ସାର', market:'ବଜାର ଦର', general:'ସାଧାରଣ' },
    weatherRain: 'ବର୍ଷା', weatherWind: 'ପବନ', weatherHumidity: 'ଆର୍ଦ୍ରତା',
    locRegistered: (loc) => `📍 ନିବନ୍ଧିତ ସ୍ଥାନ: ${loc}`,
  },
};

function t(key, ...args) {
  const lang = T[currentLang] || T.en;
  const val = lang[key] !== undefined ? lang[key] : (T.en[key] || key);
  return typeof val === 'function' ? val(...args) : val;
}

// ══════════════════════════════════════════════════════════
// APPLY UI TRANSLATIONS
// ══════════════════════════════════════════════════════════
function applyTranslations() {
  const lang = T[currentLang] || T.en;

  // Sidebar labels
  const langLabelEl = document.querySelector('.sidebar-card-title[data-i18n="langLabel"]');
  if (langLabelEl) langLabelEl.textContent = `🌐 ${lang.langLabel}`;

  const locLabelEl = document.querySelector('.sidebar-card-title[data-i18n="locationLabel"]');
  if (locLabelEl) locLabelEl.textContent = `📍 ${lang.locationLabel}`;

  const quickLabelEl = document.querySelector('.sidebar-card-title[data-i18n="quickLabel"]');
  if (quickLabelEl) quickLabelEl.textContent = `💡 ${lang.quickLabel}`;

  const weatherLabelEl = document.querySelector('.sidebar-card-title[data-i18n="weatherLabel"]');
  if (weatherLabelEl) weatherLabelEl.textContent = lang.weatherLabel;

  // Location inputs
  const locSearch = document.getElementById('locationSearch');
  if (locSearch) locSearch.placeholder = lang.locationSearch;

  // GPS button
  const gpsBtn = document.querySelector('[data-i18n="gpsBtn"]');
  if (gpsBtn) gpsBtn.textContent = lang.gpsBtn;

  // Chat title & subtitle
  const chatTitleEl = document.querySelector('.chat-title');
  if (chatTitleEl) chatTitleEl.textContent = lang.chatTitle;
  if (chatSubtitle) chatSubtitle.textContent = lang.chatSubtitle;

  // Textarea placeholder
  if (qInput) qInput.placeholder = lang.placeholder;

  // Send button
  if (!isLoading) {
    const sendTextEl = document.getElementById('sendText');
    if (sendTextEl) sendTextEl.textContent = lang.sendBtn;
  }

  // Clear button
  const clearBtnEl = document.querySelector('[data-i18n="clearBtn"]');
  if (clearBtnEl) clearBtnEl.textContent = lang.clearBtn;

  // Ctrl+Enter hint
  const hintEl = document.querySelector('.input-hint');
  if (hintEl) hintEl.textContent = lang.charHint;

  // Logout button
  const logoutBtnEl = document.querySelector('[data-i18n="logoutBtn"]');
  if (logoutBtnEl) logoutBtnEl.textContent = lang.logoutBtn;

  // Quick questions — rebuild using data-q attribute to avoid quote-escaping issues in onclick
  const qqContainer = document.querySelector('.quick-questions');
  if (qqContainer) {
    const cats = ['crop','market','pest','weather','soil','scheme','market','pest'];
    qqContainer.innerHTML = lang.quick.map((item, i) =>
      `<button class="quick-btn ${cats[i]}" data-q="${item.q.replace(/"/g,'&quot;').replace(/'/g,'&#39;')}">${item.label}</button>`
    ).join('');
    // clicks handled by document-level delegation in DOMContentLoaded
  }

  // Profile location text
  if (currentUser && (currentUser.state || currentUser.district)) {
    const loc = [currentUser.district, currentUser.state].filter(Boolean).join(', ');
    if (profileLocation) {
      profileLocation.textContent = lang.locRegistered(loc);
    }
  }
}

// ══════════════════════════════════════════════════════════
// AUTH
// ══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  const saved = sessionStorage.getItem('sf_user');
  if (saved) {
    currentUser = JSON.parse(saved);
    const savedLang = sessionStorage.getItem('sf_lang') || 'en';
    currentLang = savedLang;
    const langSel = document.getElementById('languageSelect');
    if (langSel) langSel.value = currentLang;
    showApp();
  }
  qInput && qInput.addEventListener('input', updateCharCount);

  // Wire up static quick-question buttons (data-q attribute)
  document.addEventListener('click', e => {
    const btn = e.target.closest('.quick-btn[data-q]');
    if (btn) {
      const q = btn.getAttribute('data-q');
      if (q) askQuestion(q);
    }
  });

  // Language change handler
  const langSel = document.getElementById('languageSelect');
  if (langSel) {
    langSel.addEventListener('change', function() {
      currentLang = this.value;
      sessionStorage.setItem('sf_lang', currentLang);
      applyTranslations();
    });
  }
});

function switchTab(tab) {
  document.getElementById('loginForm').classList.toggle('hidden', tab !== 'login');
  document.getElementById('registerForm').classList.toggle('hidden', tab !== 'register');
  document.getElementById('tabLogin').classList.toggle('active', tab === 'login');
  document.getElementById('tabRegister').classList.toggle('active', tab === 'register');
  document.getElementById('loginError').textContent = '';
  document.getElementById('step1Error') && (document.getElementById('step1Error').textContent = '');
  document.getElementById('step2Error') && (document.getElementById('step2Error').textContent = '');
  document.getElementById('regStep1') && document.getElementById('regStep1').classList.remove('hidden');
  document.getElementById('regStep2') && document.getElementById('regStep2').classList.add('hidden');
}

async function handleLogin(e) {
  e.preventDefault();
  const email    = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  const errEl    = document.getElementById('loginError');
  errEl.textContent = '';
  try {
    const res = await fetch(`${API}/auth/login`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.detail || 'Login failed.'; return; }
    currentUser = data.user;
    sessionStorage.setItem('sf_user', JSON.stringify(currentUser));
    showApp();
  } catch { errEl.textContent = 'Network error. Is the server running?'; }
}

async function sendOTP(isResend = false) {
  const name     = document.getElementById('regName').value.trim();
  const email    = document.getElementById('regEmail').value.trim();
  const emailC   = document.getElementById('regEmailConfirm').value.trim();
  const password = document.getElementById('regPassword').value;
  const state    = document.getElementById('regState').value;
  const district = document.getElementById('regDistrict').value.trim();
  const errEl    = document.getElementById('step1Error');
  errEl.textContent = '';

  if (!name)                { errEl.textContent = 'Please enter your full name.'; return; }
  if (!email)               { errEl.textContent = 'Please enter your email address.'; return; }
  if (email !== emailC)     { errEl.textContent = 'Email addresses do not match.'; return; }
  if (password.length < 6)  { errEl.textContent = 'Password must be at least 6 characters.'; return; }
  if (!state)               { errEl.textContent = 'Please select your state.'; return; }
  if (!district)            { errEl.textContent = 'Please enter your district.'; return; }

  const btn = document.getElementById('sendOtpBtnText');
  btn.textContent = 'Sending…';
  try {
    const res = await fetch(`${API}/auth/send-otp`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ name, email })
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.detail || 'Failed to send OTP.'; btn.textContent = 'Send Verification Code →'; return; }
    document.getElementById('regStep1').classList.add('hidden');
    document.getElementById('regStep2').classList.remove('hidden');
    const infoEl = document.getElementById('otpInfoMsg');
    if (data.demo_otp) {
      infoEl.className = 'otp-info demo';
      infoEl.innerHTML = `⚠️ <strong>Demo Mode:</strong> SMTP not configured.<br>Your OTP is: <strong style="font-size:22px;letter-spacing:5px;color:#713f12">${data.demo_otp}</strong><br><small>Add SMTP_USER + SMTP_PASSWORD in .env to send real emails.</small>`;
    } else {
      infoEl.className = 'otp-info';
      infoEl.innerHTML = `📧 A 6-digit code was sent to <strong>${email}</strong>.<br>Check your inbox (and spam folder).`;
    }
  } catch { errEl.textContent = 'Network error. Is the server running?'; }
  btn.textContent = 'Send Verification Code →';
}

function backToStep1() {
  document.getElementById('regStep2').classList.add('hidden');
  document.getElementById('regStep1').classList.remove('hidden');
  document.getElementById('step2Error').textContent = '';
  document.getElementById('otpInput').value = '';
}

async function submitRegister() {
  const email    = document.getElementById('regEmail').value.trim();
  const otp      = document.getElementById('otpInput').value.trim();
  const name     = document.getElementById('regName').value.trim();
  const password = document.getElementById('regPassword').value;
  const state    = document.getElementById('regState').value;
  const district = document.getElementById('regDistrict').value.trim();
  const errEl    = document.getElementById('step2Error');
  errEl.textContent = '';
  if (!otp || otp.length !== 6) { errEl.textContent = 'Please enter the 6-digit code.'; return; }
  try {
    const res = await fetch(`${API}/auth/register`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ name, email, password, state, district, otp })
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.detail || 'Registration failed.'; return; }
    currentUser = data.user;
    sessionStorage.setItem('sf_user', JSON.stringify(currentUser));
    showApp();
  } catch { errEl.textContent = 'Network error. Is the server running?'; }
}

function showApp() {
  authPage.classList.add('hidden');
  appPage.classList.remove('hidden');
  const firstName = currentUser.name.split(' ')[0];
  userNameDisplay.textContent = firstName;

  // Pre-fill location from profile
  if (currentUser.state || currentUser.district) {
    const loc = [currentUser.district, currentUser.state].filter(Boolean).join(', ');
    if (profileLocation) {
      const lang = T[currentLang] || T.en;
      profileLocation.textContent = lang.locRegistered(loc);
      profileLocation.style.display = 'block';
    }
    document.getElementById('locationName').value = loc;
  }

  applyTranslations();
  appendBotGreeting(firstName);
  checkHealth();
  setInterval(checkHealth, 60000);

  // If we already have coords, fetch weather + mandi immediately
  const lat = parseFloatOrNull(document.getElementById('latitude').value);
  const lon = parseFloatOrNull(document.getElementById('longitude').value);
  if (lat && lon) {
    fetchAndShowWeather(lat, lon);
    fetchAndShowMandi(null, currentUser.state || null);
  } else if (currentUser.district || currentUser.state) {
    // Geocode the registered location to get coords, then fetch
    const locStr = [currentUser.district, currentUser.state].filter(Boolean).join(', ');
    geocodeAndFetch(locStr);
  }
}

async function geocodeAndFetch(locStr) {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(locStr + ' India')}&format=json&limit=1&countrycodes=in`,
      { headers: {'Accept-Language': 'en'} }
    );
    const results = await res.json();
    if (results && results[0]) {
      const lat = parseFloat(results[0].lat);
      const lon = parseFloat(results[0].lon);
      document.getElementById('latitude').value  = lat.toFixed(4);
      document.getElementById('longitude').value = lon.toFixed(4);
      fetchAndShowWeather(lat, lon, locStr);
    }
  } catch { /* silently fail */ }
  // Always fetch mandi for state even without geocoding
  fetchAndShowMandi(null, currentUser?.state || null);
}

function logout() {
  sessionStorage.removeItem('sf_user');
  currentUser = null;
  appPage.classList.add('hidden');
  authPage.classList.remove('hidden');
  msgs.innerHTML = '';
  document.getElementById('loginEmail').value = '';
  document.getElementById('loginPassword').value = '';
  switchTab('login');
}

// ══════════════════════════════════════════════════════════
// GREETING
// ══════════════════════════════════════════════════════════
function appendBotGreeting(firstName) {
  const div = document.createElement('div');
  div.className = 'message message-bot';
  div.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-bubble">
      <strong>${escHtml(t('greeting', firstName))}</strong>
    </div>`;
  msgs.appendChild(div);
  scrollBottom();
}

// ══════════════════════════════════════════════════════════
// CHAT
// ══════════════════════════════════════════════════════════
function updateCharCount() {
  const len = qInput.value.length;
  charCount.textContent = `${len} / 2000`;
  charCount.style.color = len > 1800 ? '#da1e28' : '';
}

function handleKeyDown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); sendQuestion(); }
}

function askQuestion(q) { qInput.value = q; updateCharCount(); sendQuestion(); }

function clearChat() {
  msgs.innerHTML = '';
  if (currentUser) appendBotGreeting(currentUser.name.split(' ')[0]);
}

async function sendQuestion() {
  if (isLoading) return;
  const question = qInput.value.trim();
  if (!question) return;

  appendUserMessage(question);
  qInput.value = '';
  updateCharCount();
  showTyping();
  setLoading(true);

  const payload = {
    question,
    language: currentLang,
    location: document.getElementById('locationName').value || null,
    latitude:  parseFloatOrNull(document.getElementById('latitude').value),
    longitude: parseFloatOrNull(document.getElementById('longitude').value),
  };

  try {
    const res = await fetch(`${API}/ask`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    removeTyping();
    appendBotMessage(data);
    if (data.weather_data) updateWeatherWidget(data.weather_data);
  } catch (err) {
    removeTyping();
    appendErrorMessage(err.message);
  } finally {
    setLoading(false);
  }
}

function parseFloatOrNull(v) {
  const f = parseFloat(v);
  return isNaN(f) ? null : f;
}

function setLoading(v) {
  isLoading = v;
  sendBtn.disabled = v;
  document.getElementById('sendIcon').textContent = v ? '⏳' : '➤';
  const lang = T[currentLang] || T.en;
  document.getElementById('sendText').textContent = v ? lang.sendingBtn : lang.sendBtn;
}

// ══════════════════════════════════════════════════════════
// MESSAGE RENDERING
// ══════════════════════════════════════════════════════════
function appendUserMessage(text) {
  const d = document.createElement('div');
  d.className = 'message message-user';
  d.innerHTML = `<div class="message-avatar">👨‍🌾</div><div class="message-bubble">${escHtml(text)}</div>`;
  msgs.appendChild(d); scrollBottom();
}

function appendBotMessage(data) {
  const cat = getCatInfo(data.category);
  const pct = Math.round((data.confidence || 0.5) * 100);
  const lang = T[currentLang] || T.en;
  const d = document.createElement('div');
  d.className = 'message message-bot';
  d.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-bubble">
      <span class="category-badge ${cat.cls}">${cat.icon} ${cat.label}</span>
      <div>${fmtAnswer(data.answer)}</div>
      ${data.market_data ? buildMarketTable(data.market_data) : ''}
      ${buildSources(data.sources || [], lang.sources)}
      <div class="confidence-row">
        <span>${lang.confidence}</span>
        <div class="confidence-bar"><div class="confidence-fill" style="width:${pct}%"></div></div>
        <span>${pct}%</span>
      </div>
    </div>`;
  msgs.appendChild(d); scrollBottom();
}

function appendErrorMessage(msg) {
  const d = document.createElement('div');
  d.className = 'message message-bot';
  d.innerHTML = `
    <div class="message-avatar">⚠️</div>
    <div class="message-bubble" style="border-color:#da1e28">
      <strong style="color:#da1e28">Error</strong><br>${escHtml(msg)}
    </div>`;
  msgs.appendChild(d); scrollBottom();
}

function showTyping() {
  const d = document.createElement('div');
  d.className = 'message message-bot'; d.id = 'typingIndicator';
  const lang = T[currentLang] || T.en;
  d.innerHTML = `<div class="message-avatar">🤖</div><div class="message-bubble"><div class="dots"><span></span><span></span><span></span></div><br><small style="color:var(--gray-60)">${lang.thinkingMsg}</small></div>`;
  msgs.appendChild(d); scrollBottom();
}
function removeTyping() { const e = document.getElementById('typingIndicator'); if(e) e.remove(); }
function scrollBottom() { msgs.scrollTop = msgs.scrollHeight; }

// ══════════════════════════════════════════════════════════
// FORMATTING
// ══════════════════════════════════════════════════════════
function escHtml(t) {
  return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function fmtAnswer(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
    .replace(/^[•·]\s+(.+)$/gm,'<li>$1</li>')
    .replace(/^\d+\.\s+(.+)$/gm,'<li>$1</li>')
    .replace(/(<li>[\s\S]*?<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
    .replace(/\n/g,'<br>');
}

function getCatInfo(c) {
  const lang = T[currentLang] || T.en;
  const labels = lang.catLabels || T.en.catLabels;
  const icons = { crop:'🌾', weather:'🌤️', pest:'🐛', soil:'🌱', market:'💰', general:'📋' };
  const cls   = { crop:'cat-crop', weather:'cat-weather', pest:'cat-pest', soil:'cat-soil', market:'cat-market', general:'cat-general' };
  return {
    icon:  icons[c]  || icons.general,
    label: labels[c] || labels.general,
    cls:   cls[c]    || cls.general,
  };
}

function buildSources(sources, label) {
  if (!sources.length) return '';
  const chips = sources.slice(0,4).map(s =>
    `<span class="source-chip">📚 ${escHtml(s.source)}</span>`).join('');
  return `<div class="sources-section"><div class="sources-title">${label || 'Sources'}</div>${chips}</div>`;
}

function buildMarketTable(md) {
  if (!md?.prices?.length) return '';
  const rows = md.prices.slice(0,5).map(p =>
    `<tr><td>${escHtml(p.commodity)}</td><td>₹${Number(p.modal_price).toLocaleString('en-IN')}/Qtl</td><td style="color:var(--gray-60)">${escHtml(p.market)}</td></tr>`
  ).join('');
  return `<table class="market-table"><thead><tr><th>Commodity</th><th>Modal Price</th><th>Market</th></tr></thead><tbody>${rows}</tbody></table>`;
}

// ══════════════════════════════════════════════════════════
// LOCATION (GPS + Search)
// ══════════════════════════════════════════════════════════
function detectLocation() {
  if (!navigator.geolocation) { alert('Geolocation not supported.'); return; }
  const btn = document.querySelector('[data-i18n="gpsBtn"]');
  if (btn) btn.textContent = '⏳ Detecting…';
  navigator.geolocation.getCurrentPosition(pos => {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    document.getElementById('latitude').value  = lat.toFixed(4);
    document.getElementById('longitude').value = lon.toFixed(4);
    fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`)
      .then(r => r.json())
      .then(d => {
        const a = d.address || {};
        const name = a.city || a.town || a.village || a.county || 'Your Farm';
        const locLabel = a.state ? `${name}, ${a.state}` : name;
        document.getElementById('locationName').value = locLabel;
        if (btn) btn.textContent = t('gpsBtn');
        fetchAndShowWeather(lat, lon, locLabel);
        fetchAndShowMandi(null, a.state || null);
      }).catch(() => {
        document.getElementById('locationName').value = 'Your Farm';
        if (btn) btn.textContent = t('gpsBtn');
        fetchAndShowWeather(lat, lon);
        fetchAndShowMandi(null, null);
      });
  }, err => {
    if (btn) btn.textContent = t('gpsBtn');
    alert(`Location error: ${err.message}`);
  });
}

let _searchTimer = null;
function searchLocation(val) {
  const sugEl = document.getElementById('locationSuggestions');
  if (!val || val.length < 3) { sugEl.classList.add('hidden'); return; }
  clearTimeout(_searchTimer);
  _searchTimer = setTimeout(async () => {
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(val)}+India&format=json&limit=6&countrycodes=in`,
        { headers: {'Accept-Language': 'en'} }
      );
      const results = await res.json();
      if (!results.length) { sugEl.classList.add('hidden'); return; }
      sugEl.innerHTML = results.map(r => {
        const label = r.display_name.split(',').slice(0,3).join(', ');
        return `<div class="location-suggestion-item" onclick="selectLocation(${r.lat},${r.lon},'${escHtml(label).replace(/'/g,"\\'")}')">📍 ${escHtml(label)}</div>`;
      }).join('');
      sugEl.classList.remove('hidden');
    } catch { sugEl.classList.add('hidden'); }
  }, 400);
}

function selectLocation(lat, lon, label) {
  document.getElementById('latitude').value   = parseFloat(lat).toFixed(4);
  document.getElementById('longitude').value  = parseFloat(lon).toFixed(4);
  document.getElementById('locationName').value = label;
  document.getElementById('locationSearch').value = '';
  document.getElementById('locationSuggestions').classList.add('hidden');
  // Extract state from label for mandi
  const parts = label.split(',').map(s => s.trim());
  const stateHint = parts.length >= 2 ? parts[parts.length - 1] : null;
  fetchAndShowWeather(parseFloat(lat), parseFloat(lon), label);
  fetchAndShowMandi(null, stateHint);
}

document.addEventListener('click', e => {
  if (!e.target.closest('.location-search-wrap')) {
    const el = document.getElementById('locationSuggestions');
    if(el) el.classList.add('hidden');
  }
});

// ══════════════════════════════════════════════════════════
// WEATHER — real-time fetch + widget
// ══════════════════════════════════════════════════════════
async function fetchAndShowWeather(lat, lon, locationName) {
  if (!lat || !lon) return;
  const name = locationName || document.getElementById('locationName').value || 'Your Farm';

  // Show loading state
  weatherWidget.style.display = 'block';
  weatherContent.innerHTML = `<div style="text-align:center;padding:8px;color:var(--gray-60);font-size:12px">⏳ Loading weather…</div>`;

  try {
    const res = await fetch(`${API}/weather?latitude=${lat}&longitude=${lon}&location=${encodeURIComponent(name)}&days=7`);
    if (!res.ok) throw new Error('Weather fetch failed');
    const w = await res.json();
    updateWeatherWidget(w);
  } catch {
    weatherContent.innerHTML = `<div style="text-align:center;padding:8px;color:var(--gray-60);font-size:12px">⚠️ Weather unavailable</div>`;
  }
}

function updateWeatherWidget(w) {
  if (!w) return;
  const lang = T[currentLang] || T.en;
  const wLabel = document.querySelector('.sidebar-card-title[data-i18n="weatherLabel"]');
  if (wLabel) wLabel.textContent = lang.weatherLabel;

  // Pick a weather emoji
  const cond = (w.condition || '').toLowerCase();
  let emoji = '🌤️';
  if (cond.includes('rain') || cond.includes('shower')) emoji = '🌧️';
  else if (cond.includes('thunder') || cond.includes('storm')) emoji = '⛈️';
  else if (cond.includes('cloud') || cond.includes('overcast')) emoji = '☁️';
  else if (cond.includes('clear') || cond.includes('sunny')) emoji = '☀️';
  else if (cond.includes('fog') || cond.includes('mist')) emoji = '🌫️';
  else if (cond.includes('snow')) emoji = '❄️';

  weatherContent.innerHTML = `
    <div class="weather-location">${escHtml(w.location)}</div>
    <div class="weather-main">
      <span class="weather-emoji">${emoji}</span>
      <div>
        <div class="weather-temp">${w.temperature_max}° / ${w.temperature_min}°C</div>
        <div class="weather-condition">${escHtml(w.condition)}</div>
      </div>
    </div>
    <div class="weather-detail">
      <span>💧 ${lang.weatherRain}: ${w.precipitation}mm</span>
      <span>💨 ${lang.weatherWind}: ${w.wind_speed}km/h</span>
      ${w.humidity ? `<span>🌊 ${lang.weatherHumidity}: ${w.humidity}%</span>` : ''}
    </div>`;
  weatherWidget.style.display = 'block';
}

// ══════════════════════════════════════════════════════════
// MANDI PRICES WIDGET
// ══════════════════════════════════════════════════════════
const mandiWidget  = document.getElementById('mandiWidget');
const mandiContent = document.getElementById('mandiContent');
let _currentMandiState = null;

async function fetchAndShowMandi(commodity, state) {
  if (!mandiWidget || !mandiContent) return;
  _currentMandiState = state;

  // Show loading
  mandiWidget.style.display = 'block';
  mandiContent.innerHTML = `<div style="text-align:center;padding:8px;color:var(--gray-60);font-size:11px">⏳ Loading mandi prices…</div>`;

  const locEl = document.getElementById('mandiLocation');
  if (locEl) locEl.textContent = state ? `📍 ${state}` : '🇮🇳 National MSP';

  try {
    let url = `${API}/prices?limit=10`;
    if (commodity) url += `&commodity=${encodeURIComponent(commodity)}`;
    if (state)     url += `&state=${encodeURIComponent(state)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Mandi fetch failed');
    const prices = await res.json();
    renderMandiWidget(prices, state);
  } catch {
    mandiContent.innerHTML = `<div style="text-align:center;padding:8px;color:var(--gray-60);font-size:11px">⚠️ Prices unavailable</div>`;
  }
}

function renderMandiWidget(prices, state) {
  if (!prices || !prices.length) {
    mandiContent.innerHTML = `<div style="padding:6px;font-size:11px;color:var(--gray-60)">No price data for this region.</div>`;
    return;
  }

  const today = new Date().toLocaleDateString('en-IN');
  const isLive = prices[0]?.date && prices[0].date !== new Date().toISOString().split('T')[0]
    ? false : true;
  const badge = `<span class="mandi-static-badge">MSP 2024-25</span>`;

  const titleEl = document.getElementById('mandiWidgetTitle');
  if (titleEl) titleEl.innerHTML = `💰 Mandi Prices ${badge}`;

  const rows = prices.slice(0, 8).map(p => `
    <tr>
      <td><span class="mandi-commodity">${escHtml(p.commodity)}</span><br><span class="mandi-market">${escHtml(p.market)}</span></td>
      <td class="mandi-price">₹${Number(p.modal_price).toLocaleString('en-IN')}</td>
      <td class="mandi-market">${escHtml(p.state)}</td>
    </tr>`).join('');

  mandiContent.innerHTML = `
    <table class="mandi-table">
      <thead><tr><th>Commodity</th><th>Modal ₹/Qtl</th><th>State</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <div style="font-size:9px;color:var(--gray-60);margin-top:4px;">Updated: ${today}</div>`;
}

function refreshMandi() {
  const state = _currentMandiState ||
    (document.getElementById('locationName').value || '').split(',').pop()?.trim() || null;
  fetchAndShowMandi(null, state);
}

// ══════════════════════════════════════════════════════════
// HEALTH CHECK
// ══════════════════════════════════════════════════════════
async function checkHealth() {
  if (!healthDot) return;
  try {
    const res  = await fetch(`${API}/health`, {signal: AbortSignal.timeout(5000)});
    const data = await res.json();
    healthDot.className = 'health-dot ' + (data.granite_available ? 'green' : 'yellow');
    healthDot.title = data.message;
  } catch {
    healthDot.className = 'health-dot red';
    healthDot.title = 'Server unreachable';
  }
}
