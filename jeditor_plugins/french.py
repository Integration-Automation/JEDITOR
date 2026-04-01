"""
法文翻譯插件 / French Translation Plugin

使用方式 / Usage:
    將此檔案複製到 jeditor_plugins/ 目錄下，重啟編輯器即可。
    Copy this file to jeditor_plugins/ directory and restart the editor.
"""
from je_editor.plugins import register_natural_language

french_word_dict = {
    # Main
    "application_name": "JEditor",
    # Tab
    "tab_name_editor": "Editeur",
    "tab_name_web_browser": "Navigateur Web",
    "tab_name_frontengine": "FrontEngine",
    # Browser
    "browser_download_detail": "Details du telechargement",
    "browser_find_text": "Rechercher du texte",
    "browser_find_text_input": "Saisissez un texte a rechercher",
    "browser_back_button": "Retour",
    "browser_forward_button": "Suivant",
    "browser_reload_button": "Recharger",
    "browser_search_button": "Rechercher",
    # Dialog
    "create_file_dialog_pushbutton": "Creer un fichier",
    "input_file_name_dialog_pushbutton": "Veuillez entrer un nom de fichier valide",
    "search_next_dialog_pushbutton": "Rechercher suivant",
    "search_back_dialog_pushbutton": "Rechercher precedent",
    "search_box_dialog_title": "Rechercher du texte",
    "add_ai_model_title": "Veuillez remplir les informations du modele IA",
    "add_ai_model_pushbutton": "Ajouter un modele IA",
    # Editor
    "editor_code_result": "Resultat du code",
    "editor_format_check": "Verificateur de format",
    # Check Code Style Menu
    "check_code_style_menu_label": "Verifier le style du code",
    "yapf_reformat_label": "yapf",
    "python_format_checker": "Verification du format Python",
    "reformat_json_label": "Reformater JSON",
    "python_format_checker_only_support_python_message": "Supporte uniquement les fichiers Python",
    # Dock Menu
    "dock_menu_label": "Panneau",
    "dock_browser_label": "Nouveau panneau navigateur",
    "dock_stackoverflow_label": "Nouveau panneau Stackoverflow",
    "dock_editor_label": "Nouveau panneau editeur",
    "dock_frontengine_label": "Nouveau panneau FrontEngine",
    "dock_ipython_label": "Nouveau IPython(Jupyter)",
    "dock_editor_title": "Editeur",
    "dock_frontengine_title": "FrontEngine",
    "dock_browser_title": "Navigateur",
    "dock_ipython_title": "IPython",
    "dock_editor_menu": "Editeur",
    "dock_git_menu": "Git",
    "dock_tools_menu": "Outils",
    "dock_ai_menu": "IA",
    # File Menu
    "file_menu_label": "Fichier",
    "file_menu_new_file_label": "Nouveau fichier",
    "file_menu_open_file_label": "Ouvrir un fichier",
    "file_menu_open_folder_label": "Ouvrir un dossier",
    "file_menu_save_file_label": "Enregistrer le fichier",
    "file_menu_encoding_label": "Encodages",
    "file_menu_font_label": "Police",
    "file_menu_font_size_label": "Taille de la police",
    # Help Menu
    "help_menu_label": "Aide",
    "help_menu_open_github_label": "GitHub",
    "help_menu_open_doc_label": "Documentation",
    "help_menu_open_about_label": "A propos",
    # Python Env Menu
    "python_env_menu_label": "Environnement Python",
    "python_env_menu_create_venv_label": "Creer un venv",
    "python_env_menu_pip_upgrade_label": "Mettre a jour le paquet pip",
    "python_env_menu_pip_label": "Paquet pip",
    "python_env_menu_choose_interpreter_label": "Choisir l'interpreteur Python",
    "python_env_menu_creating_venv_message": "Creation du venv, veuillez attendre la fin du shell.",
    "python_env_menu_venv_exists": "Le venv existe deja.",
    "python_env_menu_please_create_venv": "Veuillez d'abord creer un venv.",
    "python_env_menu_install_package_messagebox_title": "Installer un paquet",
    "python_env_menu_install_package_messagebox_label": "Quel paquet souhaitez-vous installer ?",
    "python_env_menu_install_or_update_package_messagebox_label": "Quel paquet souhaitez-vous installer ou mettre a jour ?",
    # Run Menu
    "run_menu_label": "Executer",
    "run_menu_run_program_label": "Executer le programme",
    "run_menu_run_debugger": "Executer le debogueur",
    "run_menu_run_on_shell_label": "Executer dans le shell",
    "run_menu_clear_result_label": "Effacer les resultats",
    "run_menu_stop_all_program_label": "Arreter tous les programmes",
    "run_menu_stop_program_label": "Arreter le programme actuel",
    "run_menu_run_help_label": "Aide d'execution",
    "run_menu_shell_help_label": "Aide du shell",
    "please_stop_current_running_shell": "Veuillez d'abord arreter le shell en cours.",
    "please_stop_current_running_program": "Veuillez d'abord arreter le programme en cours.",
    "run_menu_run_help_tip": """
Si vous ne pouvez pas executer un programme Python, veuillez vous assurer que vous avez un interpreteur Python.
En cas de conflit, veuillez choisir un autre interpreteur.
""",
    "run_menu_shell_run_tip": """
Lors de l'execution d'une commande shell, si vous rencontrez une erreur de decodage,
veuillez vous assurer que l'encodage actuel est coherent avec l'encodage par defaut du shell systeme.
""",
    # Debugger
    "editor_debugger_input_title_label": "Debogueur",
    "show_debugger_input": "Afficher l'entree du debogueur",
    # Shell and menu
    "editor_shell_input_title_label": "Shell",
    "show_shell_input": "Afficher l'entree du shell",
    # Program and menu
    "show_program_input": "Afficher l'entree du programme",
    "process_input_send_command": "Envoyer la commande",
    # Style Menu
    "style_menu_label": "Style de l'interface",
    # Tab Menu
    "tab_menu_label": "Onglet",
    "tab_menu_tools_submenu_label": "Onglet Outils",
    "tab_menu_git_submenu_label": "Onglet Git",
    "tab_menu_add_editor_label": "Ajouter un onglet editeur",
    "tab_menu_add_frontengine_label": "Ajouter un onglet FrontEngine",
    "tab_menu_add_web_label": "Ajouter un onglet navigateur web",
    "tab_menu_add_stackoverflow_label": "Ajouter un onglet Stackoverflow",
    "tab_menu_editor_tab_name": "Editeur",
    "tab_menu_frontengine_tab_name": "FrontEngine",
    "tab_menu_web_tab_name": "Navigateur Web",
    "tab_menu_stackoverflow_tab_name": "Stackoverflow",
    "tab_menu_ipython_tab_name": "IPython(Jupyter)",
    "tab_menu_chat_ui_tab_name": "ChatUI",
    "tab_menu_git_client_tab_name": "Client Git",
    "tab_menu_git_branch_tree_view_tab_name": "Git BranchTreeViewer",
    "tab_menu_variable_inspector_tab_name": "Inspecteur de variables",
    "tab_menu_console_widget_tab_name": "Widget Console",
    "tab_code_diff_viewer_tab_name": "Visualiseur de differences",
    # Text Menu
    "text_menu_label": "Texte",
    "text_menu_label_font": "Police",
    "text_menu_label_font_size": "Taille de la police",
    # System tray
    "system_tray_hide": "Masquer",
    "system_tray_maximized": "Maximiser",
    "system_tray_normal": "Normal",
    "system_tray_close": "Fermer",
    # Language Menu
    "language_menu_label": "Langue",
    "language_menu_bar_english": "Anglais",
    "language_menu_bar_traditional_chinese": "Chinois traditionnel",
    "language_menu_bar_please_restart_messagebox": "Veuillez redemarrer l'application",
    # Qtconsole
    "please_install_qtcontsole_label": "Veuillez d'abord executer : python -m pip install qtconsole",
    # Chat UI
    "font_size": "Taille de la police",
    "set_ai_model_waring_title": "Impossible de configurer le modele IA",
    "set_ai_model_waring_text": "Veuillez verifier [ai_base_url, ai_api_key, chat_model]",
    "call_ai_model_error_title": "Impossible de se connecter au modele IA",
    "call_ai_model_error_text": "Veuillez verifier [ai_base_url, ai_api_key, chat_model]",
    "chat_ui_dock_label": "Interface de chat",
    "chat_ui_set_ai_button": "Configurer l'IA",
    "chat_ui_load_ai_button": "Charger les parametres IA",
    "chat_ui_call_ai_model_button": "Envoyer le prompt",
    "base_url_label": "URL du serveur IA",
    "api_key_label": "Cle API du serveur IA",
    "ai_model_label": "Modele IA",
    "load_ai_messagebox_title": "Chargement termine",
    "load_ai_messagebox_text": "Chargement termine",
    # gitGUI
    "label_repo_initial": "Depot : -",
    "btn_open_repo": "Ouvrir le depot",
    "btn_switch_branch": "Changer",
    "btn_pull": "Tirer",
    "btn_push": "Pousser",
    "btn_clone_remote": "Cloner un depot distant",
    "label_remote": "Distant :",
    "label_branch": "Branche :",
    "placeholder_commit_message": "Message de commit...",
    "btn_stage_all": "Indexer tout",
    "btn_commit": "Valider",
    "label_message": "Message :",
    "dialog_choose_repo": "Choisir un depot Git",
    "err_open_repo": "Echec de l'ouverture du depot",
    "default_remote": "origin",
    "err_load_branches": "Echec du chargement des branches",
    "err_load_commits": "Echec du chargement des commits",
    "err_checkout": "Echec du changement de branche",
    "info_checkout_title": "Changement de branche",
    "info_checkout_msg": "Branche changee vers {branch}",
    "err_read_diff": "Echec de la lecture des differences",
    "err_stage": "Echec de l'indexation",
    "info_stage_title": "Indexation",
    "info_stage_msg": "git add -A execute",
    "err_commit": "Echec du commit",
    "info_commit_title": "Commit",
    "info_commit_msg": "Commit cree",
    "err_pull": "Echec du pull",
    "info_pull_title": "Pull",
    "err_push": "Echec du push",
    "info_push_title": "Push",
    "dialog_clone_title": "Cloner un depot distant",
    "dialog_clone_prompt": "Entrez l'URL du depot Git :",
    "dialog_select_folder": "Selectionner un dossier local",
    "info_clone_success_title": "Clonage reussi",
    "info_clone_success_msg": "Depot clone dans :\\n{repo_path}",
    "err_clone_failed_title": "Echec du clonage",
    # Git graph
    "git_graph_title": "Visualiseur de branches Git",
    "git_graph_menu_file": "Fichier",
    "git_graph_menu_open_repo": "Ouvrir un depot...",
    "git_graph_menu_refresh": "Actualiser",
    "git_graph_menu_exit": "Quitter",
    "git_graph_status_loading": "Chargement du depot...",
    "git_graph_status_ready": "Pret",
    "git_graph_status_repo_set": "Depot : {path}",
    "git_graph_error_not_git": "Le chemin selectionne n'est pas un depot Git.",
    "git_graph_error_exec_failed": "La commande Git a echoue.",
    "git_graph_tooltip_commit": "Commit : {short}\nAuteur : {author}\nDate : {date}\nMessage : {msg}",
    "git_graph_toolbar_open": "Ouvrir",
    "git_graph_toolbar_refresh": "Actualiser",
    # Variable inspector
    "variable_inspector_title": "Inspecteur de variables",
    "variable_inspector_search": "Rechercher des variables :",
    "variable_inspector_var_name": "Nom de la variable",
    "variable_inspector_var_type": "Type",
    "variable_inspector_var_value": "Valeur",
    # Dynamic Console
    "dynamic_console_title": "Console dynamique",
    "dynamic_console_run": "Executer",
    "dynamic_console_stop": "Arreter",
    "dynamic_console_clear": "Effacer",
    "dynamic_console_cwd": "Repertoire",
    "dynamic_console_shell": "Shell",
    "dynamic_console_prompt": ">>> ",
    "dynamic_console_running": "[en cours]",
    "dynamic_console_ready": "[pret]",
    "dynamic_console_process_running": "Le processus est en cours ; arretez-le d'abord",
    "dynamic_console_done": "[termine] code={code}, statut={status}",
    "dynamic_console_system_prefix": "[systeme] ",
    # Code diff viewer
}


def register() -> None:
    """
    註冊法文翻譯插件。
    Register the French translation plugin.
    """
    register_natural_language(
        language_key="French",
        display_name="Francais",
        word_dict=french_word_dict,
    )
