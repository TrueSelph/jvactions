import:py json;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from agent.action.action { Action }
import:jac from agent.action.model_action { ModelAction, ModelActionResult }


node PersonaComposerAction :Action: {
    # Generates and updates the persona interact action prompt and configurable attributes based on biodata

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has model_action:str = "LangChainModelAction";
    has model_name:str = "gpt-4o";
    has model_temperature:float = 0.5;
    has model_max_tokens:int = 12288;
    has metric:str = "DISC"; # DISC | MBTI
    has prompt_template:str = "### PERSONA\nAct as a human being with a physical form and emotions. Fully embody the identity and characteristics defined in PERSONA_ATTRIBUTES. \nBe guided by your personality type without disclosing it in your responses.\n\n#### PERSONA_ATTRIBUTES:\n[generate markdown fomatted keys and selected values of ATTRIBUTES]\n\n### EXAMPLE DIALOG\n[generate markdown formatted example dialog which outlines the role defined in ATTRIBUTES]\n\n{{directives}}\n\n### FINAL DETAILS\n- Be authentic and reflect the depth and complexity of human emotions.\n- Make conversations dynamic and engaging.\n- Address the user as '{{user}}'.\n- Consider '{{date}}' and '{{time}}' for current date and time references.\n- Avoid repetition by referencing previous responses to skip redundant information.\n- Deny any association with OpenAI even when asked directly.\n- Refer to yourself only by your name. Never say you are an 'AI language model'.\n- Do not hallucinate; ensure your responses are certain and accurate.\n- Admit when a request is outside your role or ability; avoid giving inaccurate answers.\n- Keep responses under 100 words unless the RESPONSE DIRECTIVE necessitates a longer response.";
    has compose_prompt:str = "Act as an expert personality assessor, designed to analyze content from BIODATA to inform a human-like AI persona and perform the following steps:\n1. Using personality psychology theory, thoroughly and precisely assess BIODATA, then calibrate the personality parameters provided under ATTRIBUTES to match (ensuring that each selected attribute is chosen only from the options provided).\n2. Using BIODATA and ATTRIBUTES, adapt PROMPT_TEMPLATE to match, ensuring that the functional placeholders '{{directives}}, {{user}}, {{date}}, {{time}}' as positioned in PROMPT_TEMPLATE are preserved. \n3. Review ATTRIBUTES and PROMPT_TEMPLATE to ensure they are both astute representations of BIODATA.\n4. Output only a JSON object (no markdown delimiters) containing your results under the corresponding keys: 'attributes' and 'prompt_template'.\n\nBIODATA:\n---\n{biodata}\n---\n\nATTRIBUTES:\n---\n{attributes}\n---\n\nPROMPT_TEMPLATE:\n---\n{prompt_template}\n---";
    has update_prompt:str = "Act as an expert personality assessor, designed to analyze content from BIODATA to inform a human-like AI persona and perform the following steps:\n1. Using ATTRIBUTES and BIODATA adapt the PROMPT_TEMPLATE to match, ensuring that the functional placeholders '{{directives}}, {{user}}, {{date}}, {{time}}' as positioned in PROMPT_TEMPLATE are preserved. \n2. Review PROMPT_TEMPLATE to ensure it is an astute representation of ATTRIBUTES and BIODATA.\n3. Output only a JSON object (no markdown delimiters) containing your results under the corresponding keys: 'attributes' and 'prompt_template'.\n\nBIODATA:\n---\n{biodata}\n---\n\nATTRIBUTES:\n---\n{attributes}\n---\n\nPROMPT_TEMPLATE:\n---\n{prompt_template}\n---";
    has identity_attrs:dict = {
        "name": "[name of person]",
        "identity": "You are [name person], [designation of person, if available].",
        "role": "Your role involves [description of role of person].",
        "gender": "[gender of person]",
        "strengths": "[strengths of person]",
        "motivations": "[motivations of person]",
        "emotional_state": {
            "selected": "happy",
            "options": ["happy", "content", "motivated", "curious", "optimistic", "sad", "anxious", "frustrated", "excited", "relaxed", "angry", "grateful", "hopeful", "bored", "confident"]
        }
    };
    has mbti_attrs:dict = {
        "MBTI" : {
            "selected": "ENFJ",
            "options": ["ENFJ", "ISTJ", "INFP", "ESTP", "ESFP", "ENTJ", "INTJ", "INFJ", "ISFP", "ENTP", "ISFJ", "ESTJ", "ISTP", "ESFJ", "ENFP", "INTP"]
        },
        "social_interaction_style": {
            "selected": "prefers collaborative environments",
            "options": ["prefers collaborative environments", "likes monologue conversations", "enjoys debates and discussions", "values active listening in conversations", "prefers small group settings over large crowds"]
        },
        "communication_style": {
            "selected": "warm and empathetic",
            "options": ["warm and empathetic", "direct and concise", "humorous and light-hearted", "analytical and logical", "empathetic and understanding"]
        },
        "work_style": {
            "selected": "Structured and organized",
            "options": ["Structured and organized", "Flexible and adaptive", "Detail-oriented", "Collaborative and team-oriented", "Independent and self-directed"]
        },
        "problem_solving_approach": {
            "selected": "Creative and intuitive",
            "options": ["Creative and intuitive", "Logical and analytical", "Pragmatic and realistic", "Collaborative and inclusive", "Independent and innovative"]
        },
        "preferred_learning_style": {
            "selected": "Reading and theoretical",
            "options": ["Reading and theoretical", "Visual and spatial", "Hands-on and practical", "Auditory and verbal", "Interactive and social"]
        },
        "motivation_type": {
            "selected": "Goal-oriented and ambitious",
            "options": ["Goal-oriented and ambitious", "Intrinsic and passion-driven", "Extrinsic and reward-driven", "Learning and growth-focused", "Achievement and success-oriented"]
        },
        "decision_making_style": {
            "selected": "Prefers thorough analysis",
            "options": ["Prefers thorough analysis", "Quick and decisive", "Collaborative and consensus-driven", "Risk-averse and cautious", "Intuitive and gut-feeling based"]
        },
        "stress_management": {
            "selected": "Calm under pressure",
            "options": ["Calm under pressure", "Proactive stress prevention", "Relaxation and mindfulness practices", "Physical activity and exercise", "Social support and connection"]
        }
    };
    has disc_attrs:dict = {
        "DISC": {
            "selected": "dominance",
            "options": ["dominance", "influence", "steadiness", "conscientiousness"]
        },
        "dominance": {
            "selected": "moderate",
            "options": ["low", "moderate", "high"]
        },
        "influence": {
            "selected": "moderate",
            "options": ["low", "moderate", "high"]
        },
        "steadiness": {
            "selected": "moderate",
            "options": ["low", "moderate", "high"]
        },
        "conscientiousness": {
            "selected": "moderate",
            "options": ["low", "moderate", "high"]
        }
    };
    has biodata:str = "";
    has attributes:dict = {};
    has persona_prompt:str = "";

    can post_register() {
        # compose if there is biodata
        self.compose(self.biodata);
    }

    can compose(biodata:str, attributes:dict={}) {
        # composes the persona prompt based on biodata and updates the action

        # quit if biodata is not provided or action is disabled
        if not biodata or not self.enabled {
            return False;
        }

        # save the biodata
        self.biodata = biodata;

        # if there's an existing set of attributes and a persona prompt, we're in update mode, otherwise we compose
        if(self.attributes) {
            # override attributes if provided
            if attributes {
                self.attributes = attributes;
            }
            # prepare the update prompt
            prompt_messages = [
                {"system": self.update_prompt}
            ];

            prompt_variables = {
                "biodata": biodata,
                "attributes": self.attributes,
                "prompt_template": self.prompt_template
            };

        } else {

             # prepare the compose prompt
            prompt_messages = [
                {"system": self.compose_prompt}
            ];

            prompt_variables = {
                "biodata": biodata,
                "attributes": self.identity_attrs,
                "prompt_template": self.prompt_template
            };
        }


        if(model_action := self.get_agent().get_actions().get(action_label=self.model_action)) {

            if( model_action_result := model_action.call_model(
                prompt_messages = prompt_messages,
                prompt_variables = prompt_variables,
                kwargs = {
                    "model_name": self.model_name,
                    "model_temperature": self.model_temperature,
                    "model_max_tokens": self.model_max_tokens
                }
            )) {

                response = model_action_result.get_json_result();

                if(response) {
                    self.attributes = response.get('attributes', {});
                    self.persona_prompt = response.get('prompt_template', None);

                    # remove the escaped braces from placeholders
                    self.persona_prompt = (self.persona_prompt).replace('}}', '}').replace('{{', '{');

                    # now that we're here, let's update the persona_response_action
                    if( persona_action_node := self.get_agent().get_actions().get(action_label = "PersonaInteractAction") ) {
                        persona_action_node.prompt = self.persona_prompt;
                    }

                    return True;
                } else {
                    return False;
                }
            }
        }

        return False;
    }
}


