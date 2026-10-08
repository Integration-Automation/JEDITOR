"""
設定 AI 供應者的對話框
The dialog for configuring the AI providers.

每個供應者各有一組設定。對話框預設只把設定套用到這次執行，不寫進磁碟：API 金鑰
只會存在使用者自己放的地方。要存檔得自己勾選，而且勾選處會說明金鑰是明文。
Each provider has a group of settings of its own. By default the dialog applies
them to this run only and writes nothing to disk, so an API key is only ever
stored where the user put it. Saving has to be ticked, and the tick box says the
key is kept as plain text.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QWidget
)

from je_editor.adapters.ai.settings_file import save_ai_settings
from je_editor.core.services.editor_services import EditorServices
from je_editor.utils.exception.exceptions import JEditorServiceException
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class SetAIDialog(QWidget):
    """
    設定 AI 供應者
    Configure the AI providers.
    """

    # 設定套用之後發出 / Fired after the settings were applied
    settings_applied = Signal()

    def __init__(self, services: EditorServices, provider: str = "") -> None:
        """
        :param services: 持有 AI 設定與供應者登記表的核心服務
            the core services holding the AI settings and the provider registry
        :param provider: 一開始要顯示哪個供應者 / the provider to show first
        """
        jeditor_logger.info("Init SetAIDialog")
        super().__init__()
        self._services = services
        word = language_wrapper.language_word_dict

        self.provider_label = QLabel(word.get("chat_ui_provider_label"))
        self.provider_combobox = QComboBox()
        self.provider_combobox.addItems(services.ai_providers.names())
        self.base_url_label = QLabel(word.get("base_url_label"))
        self.base_url_input = QLineEdit()
        self.api_key_label = QLabel(word.get("api_key_label"))
        self.api_key_input = QLineEdit()
        # 金鑰不該在畫面上被旁人看到 / A key should not be readable over the user's shoulder
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.chat_model_label = QLabel(word.get("ai_model_label"))
        self.chat_model_input = QLineEdit()
        self.system_prompt_label = QLabel(word.get("ai_system_prompt_label"))
        self.system_prompt_input = QPlainTextEdit()
        self.save_to_file_checkbox = QCheckBox(word.get("ai_save_to_file_checkbox"))
        self.add_ai_info_button = QPushButton(word.get("ai_apply_settings_button"))
        self.add_ai_info_button.clicked.connect(self.update_ai_config)

        self.grid_layout = QGridLayout()
        fields = (
            (self.provider_label, self.provider_combobox),
            (self.base_url_label, self.base_url_input),
            (self.api_key_label, self.api_key_input),
            (self.chat_model_label, self.chat_model_input),
            (self.system_prompt_label, self.system_prompt_input),
        )
        for row, (label, field) in enumerate(fields):
            self.grid_layout.addWidget(label, row, 0)
            self.grid_layout.addWidget(field, row, 1)
        self.grid_layout.addWidget(self.save_to_file_checkbox, len(fields), 1)
        self.grid_layout.addWidget(self.add_ai_info_button, len(fields) + 1, 1)
        self.setWindowTitle(word.get("add_ai_model_title"))
        self.setLayout(self.grid_layout)

        if provider in services.ai_providers:
            self.provider_combobox.setCurrentText(provider)
        self.provider_combobox.currentIndexChanged.connect(self.show_provider_settings)
        self.show_provider_settings()

    def show_provider_settings(self) -> None:
        """把目前選的供應者的設定填進欄位 / Fill the fields with the settings of the provider picked."""
        settings = self._services.ai_settings.settings_for(self.provider_combobox.currentText())
        self.base_url_input.setText(settings.base_url)
        self.api_key_input.setText(settings.api_key)
        self.chat_model_input.setText(settings.model)
        self.system_prompt_input.setPlainText(settings.system_prompt)

    def update_ai_config(self) -> bool:
        """
        套用欄位裡的設定，並把這個供應者設為目前使用的
        Apply what the fields hold and make this provider the one in use.

        每個欄位都可以留空：金鑰留空表示交給供應者自己從環境找，位址與模型留空
        表示用供應者的預設。
        Every field may be left empty: no key leaves the provider to find one in
        the environment, and no address or model means the provider's default.

        :return: 是否套用成功（要求存檔而存不進去時為 ``False``）
            whether it was applied; ``False`` when saving was asked for and failed
        """
        provider = self.provider_combobox.currentText()
        if not provider:
            return False
        settings = self._services.ai_settings
        settings.update(
            provider,
            base_url=self.base_url_input.text().strip(),
            api_key=self.api_key_input.text().strip(),
            model=self.chat_model_input.text().strip(),
            system_prompt=self.system_prompt_input.toPlainText().strip(),
        )
        settings.active_provider = provider
        word = language_wrapper.language_word_dict
        if self.save_to_file_checkbox.isChecked():
            try:
                save_ai_settings(settings)
            except JEditorServiceException as error:
                QMessageBox.warning(self, word.get("set_ai_model_waring_title"), str(error))
                return False
        self.settings_applied.emit()
        self.close()
        return True
