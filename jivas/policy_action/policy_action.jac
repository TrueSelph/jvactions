import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.action.action { Action }

node PolicyAction :Action: {
    # Manages AI policy document serving for an Agent

    has content: str = """
    # AI Policy - {agent_name}

    ### 1. Introduction

    At TrueSelph Inc, we are committed to providing a seamless and secure experience with our AI-powered virtual assistant referred to as a ‘Selph’. This AI policy outlines our principles and practices to ensure user privacy, data protection, and responsible AI usage.

    ### 2. User Consent

    The Selph operates on WhatsApp, and by using our service, you consent to the terms outlined in this policy. We prioritize user consent and will never use your data without your explicit permission.

    ### 3. Data Privacy

    #### Data Collection
    This Selph may collect user data, including messages, voice recordings, and user interactions, solely for the purpose of delivering personalized responses.

    #### Data Security
    We employ robust security measures to protect your data from unauthorized access, breaches, or misuse. Our data handling complies with all relevant data protection laws. We anonymize and obfuscate all sensitive information within chats which may be logged for analytics. Our platform does not persist or archive voice notes or recorded speech.

    #### Data Sharing
    We do not share your personal data with third parties unless required by law or with your explicit consent.

    ### 4. Transparency

    #### Explainability
    We aim to make this Selph's actions and responses transparent and understandable. If you have questions about how this Selph operates, please [contact our support team](https://wa.me/+5926214954).

    #### AI Decision-Making
    While AI powers this Selph, human oversight ensures that AI-driven decisions align with ethical and legal standards.

    ### 5. Responsiveness to User Concerns

    We value user feedback and are committed to addressing any concerns or inquiries promptly. You can reach out to our support team [through WhatsApp](https://wa.me/+5926214954) or email us at hello@trueselph.com.

    ### 6. User Rights

    #### Data Access
    You have the right to access the data collected by this Selph and request its deletion.

    #### Data Correction and Accuracy
    You can request corrections to inaccurate or incomplete data. We strive to maintain data accuracy and will make every effort to correct inaccuracies promptly. If you believe any information provided by this Selph is inaccurate, [please inform us immediately](https://wa.me/+5926214954).


    ### 7. Ethical Usage

    This Selph is designed to provide helpful information and services. It will not engage in harmful, offensive, or illegal activities. We strictly prohibit the use of this Selph for any malicious purposes.

    ### 8. Compliance with Laws

    We comply with all applicable data protection, privacy, and AI ethics laws and regulations in your region.

    ### 9. Continuous Improvement

    We are committed to continually improving this Selph's capabilities, user experience, and privacy measures. This policy will be updated accordingly.

    ### 10. Contact Information

    If you have questions or concerns about this AI policy or this Selph's operations, please reach out to our support team [through WhatsApp](https://wa.me/+5926214954) or email us at hello@trueselph.com.

    By interacting with this Selph, you acknowledge and agree to the terms outlined in this AI policy. We appreciate your trust in us and are dedicated to providing you with a safe and reliable virtual assistant experience.

    TrueSelph Inc.
    14 March, 2024

    """;

}
