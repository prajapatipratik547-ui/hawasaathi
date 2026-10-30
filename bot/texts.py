"""All bot messages, one dict per language (en, hi, mr)."""

from urllib.parse import quote

BOT_LINK = "https://t.me/HawaSaathiBot"

# shown before the user has picked a language, so it's in all three
WELCOME = "Welcome to HawaSaathi! Please choose a language / कृपया भाषा चुनें / कृपया भाषा निवडा"

TEXTS = {
    "en": {
        "ask_location": "Share your location with the button below, or type your area and city (e.g. Kothrud, Pune).",
        "share_location": "📍 Share location",
        "place_not_found": "I couldn't find that place. Check the spelling and try again (e.g. Kothrud, Pune), or tap 📍 Share location below.",
        "no_data": "Sorry, I couldn't find air-quality data for that location.",
        "not_enough_data": "Sorry, there isn't enough data to work out the AQI for that location.",
        "your_area": "Your area",
        "aqi_reply": (
            "📍 Area: {area}\n"
            "Air quality (India AQI): {aqi} – {category}\n"
            "PM2.5: {pm25} µg/m³ · PM10: {pm10} µg/m³\n"
            "Source: Open-Meteo (satellite/model estimate)"
        ),
        "q_age_group": "A few quick questions so I can give advice that fits you.\n\n1/3 · Which age group are you in?",
        "age_group_child": "Child (under 14)",
        "age_group_adult": "Adult",
        "age_group_senior": "60+",
        "q_condition": "2/3 · Do you have any of these health conditions?",
        "condition_none": "None",
        "condition_lung": "Asthma or lung",
        "condition_heart": "Heart",
        "condition_pregnant": "Pregnant",
        "q_outdoor_worker": "3/3 · Do you work outdoors most of the day?",
        "outdoor_worker_yes": "Yes",
        "outdoor_worker_no": "No",
        "all_set": "All set! I'll send your air update every morning at 7 AM.\nSend /settings to change your details.",
        "fallback": "I didn't understand that. Send /start to begin.",
        "error": "Sorry, something went wrong. Please try again in a minute.",
        "answered_age_group": "1/3 · Age group: {answer} ✅",
        "answered_condition": "2/3 · Health condition: {answer} ✅",
        "answered_outdoor_worker": "3/3 · Work outdoors: {answer} ✅",
        # alerts
        "morning_alert": "🌅 Good morning! Air in {area} today: {emoji} {category} (India AQI {aqi})",
        "spike_alert": "⚠️ Air alert for {area}: {emoji} {category} (India AQI {aqi}) right now.",
        "for_you": "For you ({who}): {advice}",
        "for_you_plain": "For you: {advice}",
        "best_time": "✅ Best time to go out: {time}",
        "disclaimer": "Not medical advice. If you have trouble breathing, call 108.",
        "fb_yes": "✅ Yes, it changed my plan",
        "fb_no": "❌ No",
        "thanks": "Thanks!",
        "who_child": "child",
        "who_senior": "60+",
        "who_lung": "asthma/lung",
        "who_heart": "heart condition",
        "who_pregnant": "pregnancy",
        "who_outdoor": "outdoor work",
        # advice: tip_0..tip_5 follow the AQI level (Good..Severe)
        "tip_0": "Air is clean. A great day to be outside.",
        "tip_1": "Air is fine for most people. Enjoy your time outdoors.",
        "tip_2": "Avoid long or hard exercise outdoors, and close windows during peak traffic hours.",
        "tip_3": "Avoid morning walks and outdoor exercise. Wear an N95 mask outdoors and keep windows closed.",
        "tip_4": "Stay indoors as much as you can. Wear an N95 mask if you must go out.",
        "tip_5": "Stay indoors and avoid all outdoor activity. Wear an N95 mask if you must step out.",
        "tip_lung": "Keep your inhaler with you.",
        "tip_heart": "Avoid heavy effort outdoors, and rest if you feel unwell.",
        "tip_pregnant": "Spend less time outdoors and rest indoors.",
        "tip_child": "Keep kids' outdoor play short.",
        "tip_senior": "Walk indoors, or at the cleanest time of day.",
        "tip_outdoor": "Take breaks in cleaner hours and wear an N95 mask while working.",
        # questions (AI agent)
        "question_limit": "You've asked {limit} questions today, which is the daily limit. Please ask again tomorrow! Your morning air update will still come as usual.",
        "fallback_answer": "I can't give a full answer right now, but here's the air in {area}: {emoji} {category} (India AQI {aqi}).",
        "agent_unavailable": "Sorry, I can't answer right now. Please try again in a few minutes.",
        # voice messages
        "voice_heard": "🎙️ I heard: “{text}”",
        "voice_failed": "Sorry, I couldn't understand that voice message. Please try again, or type it.",
        "voice_too_long": "Please keep voice messages under {seconds} seconds.",
        # /delete
        "delete_confirm": "This permanently deletes everything HawaSaathi stores about you: your location, profile, alerts, answers and questions. Are you sure?",
        "delete_yes": "🗑️ Yes, delete my data",
        "delete_no": "Cancel",
        "deleted": "Done. All your data has been deleted and you won't get any more alerts. Send /start any time to use HawaSaathi again.",
        "delete_cancelled": "Cancelled. Nothing was deleted.",
        # invite
        "invite_text": "Know someone who should get these alerts? Parents, kids, a friend with asthma? Share HawaSaathi with them 👇",
        "invite_button": "👨‍👩‍👧 Invite your family",
        "share_message": "HawaSaathi is a free Telegram bot that sends a daily air-quality alert for your area, with advice for your health (English, हिंदी, मराठी). Try it:",
        "category": {
            "Good": "Good",
            "Satisfactory": "Satisfactory",
            "Moderate": "Moderate",
            "Poor": "Poor",
            "Very Poor": "Very Poor",
            "Severe": "Severe",
        },
    },
    "hi": {
        "ask_location": "नीचे दिए बटन से अपनी लोकेशन भेजें, या अपना इलाका और शहर लिखें (जैसे: Kothrud, Pune)।",
        "share_location": "📍 लोकेशन भेजें",
        "place_not_found": "वह जगह नहीं मिली। स्पेलिंग जाँचकर फिर से लिखें (जैसे: Kothrud, Pune), या नीचे 📍 लोकेशन भेजें बटन दबाएँ।",
        "no_data": "माफ़ कीजिए, इस जगह के लिए हवा की गुणवत्ता का डेटा नहीं मिला।",
        "not_enough_data": "माफ़ कीजिए, इस जगह का AQI निकालने के लिए पर्याप्त डेटा नहीं है।",
        "your_area": "आपका इलाका",
        "aqi_reply": (
            "📍 इलाका: {area}\n"
            "हवा की गुणवत्ता (भारतीय AQI): {aqi} – {category}\n"
            "PM2.5: {pm25} µg/m³ · PM10: {pm10} µg/m³\n"
            "स्रोत: Open-Meteo (सैटेलाइट/मॉडल अनुमान)"
        ),
        "q_age_group": "कुछ छोटे सवाल, ताकि मैं आपके लिए सही सलाह दे सकूँ।\n\n1/3 · आपका आयु वर्ग क्या है?",
        "age_group_child": "बच्चा (14 से कम)",
        "age_group_adult": "वयस्क",
        "age_group_senior": "60+",
        "q_condition": "2/3 · क्या आपको इनमें से कोई स्वास्थ्य समस्या है?",
        "condition_none": "कोई नहीं",
        "condition_lung": "अस्थमा या फेफड़े",
        "condition_heart": "दिल",
        "condition_pregnant": "गर्भवती",
        "q_outdoor_worker": "3/3 · क्या आप दिन का ज़्यादातर समय बाहर काम करते हैं?",
        "outdoor_worker_yes": "हाँ",
        "outdoor_worker_no": "नहीं",
        "all_set": "सब तैयार! मैं हर सुबह 7 बजे आपको हवा का अपडेट भेजूँगा।\nबदलाव करने के लिए /settings भेजें।",
        "fallback": "मैं समझ नहीं पाया। शुरू करने के लिए /start भेजें।",
        "error": "माफ़ कीजिए, कुछ गड़बड़ हो गई। कृपया एक मिनट बाद फिर कोशिश करें।",
        "answered_age_group": "1/3 · आयु वर्ग: {answer} ✅",
        "answered_condition": "2/3 · स्वास्थ्य समस्या: {answer} ✅",
        "answered_outdoor_worker": "3/3 · बाहर काम: {answer} ✅",
        # alerts
        "morning_alert": "🌅 सुप्रभात! आज {area} की हवा: {emoji} {category} (भारतीय AQI {aqi})",
        "spike_alert": "⚠️ {area} में हवा की चेतावनी: अभी {emoji} {category} (भारतीय AQI {aqi})।",
        "for_you": "आपके लिए ({who}): {advice}",
        "for_you_plain": "आपके लिए: {advice}",
        "best_time": "✅ बाहर जाने का सबसे अच्छा समय: {time}",
        "disclaimer": "यह डॉक्टरी सलाह नहीं है। साँस लेने में तकलीफ़ हो तो 108 पर कॉल करें।",
        "fb_yes": "✅ हाँ, इससे मेरा प्लान बदला",
        "fb_no": "❌ नहीं",
        "thanks": "धन्यवाद!",
        "who_child": "बच्चा",
        "who_senior": "60+",
        "who_lung": "अस्थमा/फेफड़े",
        "who_heart": "दिल की समस्या",
        "who_pregnant": "गर्भावस्था",
        "who_outdoor": "बाहर काम",
        # advice: tip_0..tip_5 follow the AQI level (Good..Severe)
        "tip_0": "हवा साफ़ है। बाहर जाने के लिए बढ़िया दिन है।",
        "tip_1": "ज़्यादातर लोगों के लिए हवा ठीक है। बाहर का आनंद लें।",
        "tip_2": "बाहर लंबी या भारी कसरत से बचें, और ज़्यादा ट्रैफ़िक के समय खिड़कियाँ बंद रखें।",
        "tip_3": "सुबह की सैर और बाहर कसरत से बचें। बाहर N95 मास्क पहनें और खिड़कियाँ बंद रखें।",
        "tip_4": "जितना हो सके घर के अंदर रहें। बाहर जाना ज़रूरी हो तो N95 मास्क पहनें।",
        "tip_5": "घर के अंदर रहें और बाहर की हर गतिविधि से बचें। बाहर निकलना ज़रूरी हो तो N95 मास्क पहनें।",
        "tip_lung": "अपना इनहेलर साथ रखें।",
        "tip_heart": "बाहर भारी मेहनत से बचें, और तबीयत ठीक न लगे तो आराम करें।",
        "tip_pregnant": "बाहर कम समय बिताएँ और घर के अंदर आराम करें।",
        "tip_child": "बच्चों का बाहर खेलना कम समय के लिए रखें।",
        "tip_senior": "सैर घर के अंदर करें, या दिन के सबसे साफ़ समय पर करें।",
        "tip_outdoor": "साफ़ हवा वाले समय में ब्रेक लें और काम करते समय N95 मास्क पहनें।",
        # questions (AI agent)
        "question_limit": "आज आप {limit} सवाल पूछ चुके हैं, जो एक दिन की सीमा है। कृपया कल फिर पूछें! सुबह का हवा अपडेट हमेशा की तरह आएगा।",
        "fallback_answer": "अभी मैं पूरा जवाब नहीं दे पा रहा, लेकिन {area} की हवा अभी: {emoji} {category} (भारतीय AQI {aqi})।",
        "agent_unavailable": "माफ़ कीजिए, अभी मैं जवाब नहीं दे पा रहा। कृपया कुछ मिनट बाद फिर पूछें।",
        # voice messages
        "voice_heard": "🎙️ मैंने सुना: “{text}”",
        "voice_failed": "माफ़ कीजिए, यह वॉइस मैसेज समझ नहीं आया। कृपया फिर से बोलें, या लिखकर भेजें।",
        "voice_too_long": "कृपया वॉइस मैसेज {seconds} सेकंड से छोटा रखें।",
        # /delete
        "delete_confirm": "इससे HawaSaathi में सेव आपकी सारी जानकारी हमेशा के लिए मिट जाएगी: लोकेशन, प्रोफ़ाइल, अलर्ट, जवाब और सवाल। क्या आप पक्का ऐसा करना चाहते हैं?",
        "delete_yes": "🗑️ हाँ, मेरा डेटा मिटाएँ",
        "delete_no": "रद्द करें",
        "deleted": "हो गया। आपका सारा डेटा मिटा दिया गया है, और अब आपको अलर्ट नहीं आएँगे। HawaSaathi फिर से इस्तेमाल करने के लिए कभी भी /start भेजें।",
        "delete_cancelled": "रद्द किया गया। कुछ भी नहीं मिटाया गया।",
        # invite
        "invite_text": "किसे ये अलर्ट मिलने चाहिए? माता-पिता, बच्चे, अस्थमा वाले दोस्त? उनके साथ HawaSaathi शेयर करें 👇",
        "invite_button": "👨‍👩‍👧 परिवार को बुलाएँ",
        "share_message": "HawaSaathi एक मुफ़्त Telegram बॉट है जो आपके इलाके की हवा का रोज़ अलर्ट और आपकी सेहत के हिसाब से सलाह देता है (English, हिंदी, मराठी)। आज़माएँ:",
        "category": {
            "Good": "अच्छा",
            "Satisfactory": "संतोषजनक",
            "Moderate": "मध्यम",
            "Poor": "खराब",
            "Very Poor": "बहुत खराब",
            "Severe": "गंभीर",
        },
    },
    "mr": {
        "ask_location": "खालील बटणाने तुमचे लोकेशन पाठवा, किंवा तुमचा भाग आणि शहर लिहा (उदा. Kothrud, Pune).",
        "share_location": "📍 लोकेशन पाठवा",
        "place_not_found": "ती जागा सापडली नाही. स्पेलिंग तपासून पुन्हा लिहा (उदा. Kothrud, Pune), किंवा खालील 📍 लोकेशन पाठवा बटण दाबा.",
        "no_data": "माफ करा, या ठिकाणासाठी हवेच्या गुणवत्तेचा डेटा मिळाला नाही.",
        "not_enough_data": "माफ करा, या ठिकाणाचा AQI काढण्यासाठी पुरेसा डेटा नाही.",
        "your_area": "तुमचा भाग",
        "aqi_reply": (
            "📍 भाग: {area}\n"
            "हवेची गुणवत्ता (भारतीय AQI): {aqi} – {category}\n"
            "PM2.5: {pm25} µg/m³ · PM10: {pm10} µg/m³\n"
            "स्रोत: Open-Meteo (उपग्रह/मॉडेल अंदाज)"
        ),
        "q_age_group": "काही छोटे प्रश्न, म्हणजे मी तुम्हाला योग्य सल्ला देऊ शकेन.\n\n1/3 · तुमचा वयोगट कोणता?",
        "age_group_child": "मूल (14 पेक्षा कमी)",
        "age_group_adult": "प्रौढ",
        "age_group_senior": "60+",
        "q_condition": "2/3 · तुम्हाला यापैकी कोणता आरोग्याचा त्रास आहे का?",
        "condition_none": "काहीही नाही",
        "condition_lung": "दमा किंवा फुफ्फुस",
        "condition_heart": "हृदय",
        "condition_pregnant": "गर्भवती",
        "q_outdoor_worker": "3/3 · तुम्ही दिवसाचा बहुतेक वेळ बाहेर काम करता का?",
        "outdoor_worker_yes": "हो",
        "outdoor_worker_no": "नाही",
        "all_set": "सगळं तयार! मी दररोज सकाळी 7 वाजता तुम्हाला हवेचा अपडेट पाठवेन.\nबदल करण्यासाठी /settings पाठवा.",
        "fallback": "मला समजलं नाही. सुरू करण्यासाठी /start पाठवा.",
        "error": "माफ करा, काहीतरी चूक झाली. कृपया एका मिनिटाने पुन्हा प्रयत्न करा.",
        "answered_age_group": "1/3 · वयोगट: {answer} ✅",
        "answered_condition": "2/3 · आरोग्याचा त्रास: {answer} ✅",
        "answered_outdoor_worker": "3/3 · बाहेरचे काम: {answer} ✅",
        # alerts
        "morning_alert": "🌅 सुप्रभात! आज {area} मधील हवा: {emoji} {category} (भारतीय AQI {aqi})",
        "spike_alert": "⚠️ {area} मध्ये हवेचा इशारा: आत्ता {emoji} {category} (भारतीय AQI {aqi}).",
        "for_you": "तुमच्यासाठी ({who}): {advice}",
        "for_you_plain": "तुमच्यासाठी: {advice}",
        "best_time": "✅ बाहेर जाण्याची सर्वोत्तम वेळ: {time}",
        "disclaimer": "हा वैद्यकीय सल्ला नाही. श्वास घेण्यास त्रास होत असेल तर 108 वर कॉल करा.",
        "fb_yes": "✅ हो, यामुळे माझा प्लॅन बदलला",
        "fb_no": "❌ नाही",
        "thanks": "धन्यवाद!",
        "who_child": "मूल",
        "who_senior": "60+",
        "who_lung": "दमा/फुफ्फुस",
        "who_heart": "हृदयाचा त्रास",
        "who_pregnant": "गर्भावस्था",
        "who_outdoor": "बाहेरचे काम",
        # advice: tip_0..tip_5 follow the AQI level (Good..Severe)
        "tip_0": "हवा स्वच्छ आहे. बाहेर जाण्यासाठी उत्तम दिवस.",
        "tip_1": "बहुतेक लोकांसाठी हवा ठीक आहे. बाहेरचा आनंद घ्या.",
        "tip_2": "बाहेर जास्त वेळ किंवा जड व्यायाम टाळा, आणि जास्त रहदारीच्या वेळी खिडक्या बंद ठेवा.",
        "tip_3": "सकाळचे फिरणे आणि बाहेरचा व्यायाम टाळा. बाहेर N95 मास्क वापरा आणि खिडक्या बंद ठेवा.",
        "tip_4": "शक्य तितके घरातच राहा. बाहेर जावेच लागले तर N95 मास्क वापरा.",
        "tip_5": "घरातच राहा आणि बाहेरच्या सर्व हालचाली टाळा. बाहेर पडावेच लागले तर N95 मास्क वापरा.",
        "tip_lung": "तुमचा इनहेलर सोबत ठेवा.",
        "tip_heart": "बाहेर जास्त श्रम टाळा, आणि बरे वाटत नसेल तर विश्रांती घ्या.",
        "tip_pregnant": "बाहेर कमी वेळ घालवा आणि घरात विश्रांती घ्या.",
        "tip_child": "मुलांचे बाहेर खेळणे थोड्या वेळापुरते ठेवा.",
        "tip_senior": "फिरणे घरातच करा, किंवा दिवसाच्या सर्वात स्वच्छ वेळी करा.",
        "tip_outdoor": "स्वच्छ हवेच्या वेळेत विश्रांती घ्या आणि काम करताना N95 मास्क वापरा.",
        # questions (AI agent)
        "question_limit": "आज तुम्ही {limit} प्रश्न विचारले आहेत, ही एका दिवसाची मर्यादा आहे. कृपया उद्या पुन्हा विचारा! सकाळचा हवेचा अपडेट नेहमीप्रमाणे येईल.",
        "fallback_answer": "आत्ता मी सविस्तर उत्तर देऊ शकत नाही, पण {area} मधील हवा आत्ता: {emoji} {category} (भारतीय AQI {aqi}).",
        "agent_unavailable": "माफ करा, आत्ता मी उत्तर देऊ शकत नाही. कृपया काही मिनिटांनी पुन्हा विचारा.",
        # voice messages
        "voice_heard": "🎙️ मी ऐकले: “{text}”",
        "voice_failed": "माफ करा, हा व्हॉइस मेसेज समजला नाही. कृपया पुन्हा बोला, किंवा लिहून पाठवा.",
        "voice_too_long": "कृपया व्हॉइस मेसेज {seconds} सेकंदांपेक्षा लहान ठेवा.",
        # /delete
        "delete_confirm": "यामुळे HawaSaathi मध्ये जतन केलेली तुमची सर्व माहिती कायमची हटवली जाईल: लोकेशन, प्रोफाइल, अलर्ट, उत्तरे आणि प्रश्न. तुम्हाला खात्री आहे का?",
        "delete_yes": "🗑️ हो, माझा डेटा हटवा",
        "delete_no": "रद्द करा",
        "deleted": "झाले. तुमचा सर्व डेटा हटवला आहे, आणि आता तुम्हाला अलर्ट येणार नाहीत. HawaSaathi पुन्हा वापरण्यासाठी कधीही /start पाठवा.",
        "delete_cancelled": "रद्द केले. काहीही हटवले नाही.",
        # invite
        "invite_text": "हे अलर्ट कोणाला मिळायला हवेत? आई-वडील, मुले, दमा असलेले मित्र? त्यांच्यासोबत HawaSaathi शेअर करा 👇",
        "invite_button": "👨‍👩‍👧 कुटुंबाला बोलवा",
        "share_message": "HawaSaathi हा एक मोफत Telegram बॉट आहे जो तुमच्या भागातील हवेचा रोजचा अलर्ट आणि तुमच्या आरोग्यानुसार सल्ला देतो (English, हिंदी, मराठी). वापरून पाहा:",
        "category": {
            "Good": "चांगली",
            "Satisfactory": "समाधानकारक",
            "Moderate": "मध्यम",
            "Poor": "वाईट",
            "Very Poor": "खूप वाईट",
            "Severe": "गंभीर",
        },
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Get a message in the user's language (English if unknown), filling in {placeholders}."""
    texts = TEXTS.get(lang) or TEXTS["en"]
    return texts[key].format(**kwargs) if kwargs else texts[key]


def category_name(lang: str, category: str) -> str:
    texts = TEXTS.get(lang) or TEXTS["en"]
    return texts["category"].get(category, category)


def share_url(lang: str) -> str:
    """Telegram's share screen, pre-filled with an invite to the bot in the user's language."""
    return f"https://t.me/share/url?url={quote(BOT_LINK)}&text={quote(t(lang, 'share_message'))}"
