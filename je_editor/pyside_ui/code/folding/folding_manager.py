"""
程式碼折疊管理器（Qt 整合層）
Code folding manager (Qt integration layer).

折疊只切換 ``QTextBlock`` 的可見性，永遠不會修改文字內容，因此存檔與
``toPlainText()`` 一律取得完整內容，折疊不可能造成資料遺失。
Folding only toggles ``QTextBlock`` visibility and never edits text, so saving and
``toPlainText()`` always return the full content — folding can never lose data.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from je_editor.utils.code_folding.brace_regions import fold_regions_for
from je_editor.utils.code_folding.fold_regions import FoldRegion, region_at_line
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor


class FoldingManager:
    """
    管理單一編輯器的折疊狀態
    Manage the fold state of one editor.

    折疊狀態以「被折疊的標頭行號集合」表示。重新套用時一律先讓所有行可見，
    再隱藏仍然有效的折疊區塊，因此絕不會殘留被錯誤隱藏的行（自我修復）。
    Fold state is the set of folded header line numbers. Re-applying always makes
    every line visible first, then hides only still-valid folded regions, so a line
    can never be left wrongly hidden (self-healing).
    """

    def __init__(self, editor: CodeEditor) -> None:
        """
        :param editor: 被管理的程式碼編輯器 / The code editor being managed
        """
        self._editor = editor
        self._folded_headers: set[int] = set()

    def compute_regions(self) -> list[FoldRegion]:
        """
        依目前文字計算所有可折疊區塊
        Compute every foldable region for the current text.

        折疊方式依語言而定：以大括號劃分區塊的語言看括號配對，其餘看縮排。
        How the regions are found depends on the language: brace-delimited ones
        follow their pairs, and everything else follows indentation.

        :return: 可折疊區塊清單 / The list of foldable regions
        """
        text = self._editor.toPlainText()
        return fold_regions_for(text.split("\n"), self._suffix())

    def _suffix(self) -> str:
        """目前檔案的副檔名 / The current file's suffix."""
        current = getattr(self._editor, "current_file", None)
        return Path(str(current)).suffix if current else ""

    def foldable_header_lines(self) -> set[int]:
        """
        取得所有可折疊標頭的行號
        Return the header line numbers of every foldable region.

        :return: 標頭行號集合（0 起算）/ Header line numbers (0-based)
        """
        return {region.start for region in self.compute_regions()}

    def is_folded(self, line: int) -> bool:
        """
        判斷某個標頭目前是否為折疊狀態
        Return whether a header line is currently folded.

        :param line: 標頭行號（0 起算）/ The header line (0-based)
        :return: 折疊時為 ``True`` / ``True`` when folded
        """
        return line in self._folded_headers

    def is_any_folded(self) -> bool:
        """
        判斷是否有任何折疊中的區塊
        Return whether any region is currently folded.

        :return: 有折疊時為 ``True`` / ``True`` when at least one region is folded
        """
        return bool(self._folded_headers)

    def folded_header_lines(self) -> set[int]:
        """
        取得目前折疊中的標頭行號
        Return the header line numbers that are currently folded.

        :return: 折疊中的標頭行號集合（0 起算）/ Folded header line numbers (0-based)
        """
        return set(self._folded_headers)

    def toggle_fold(self, line: int) -> bool:
        """
        切換指定標頭的折疊狀態
        Toggle the fold state of a header line.

        :param line: 標頭行號（0 起算）/ The header line (0-based)
        :return: 該行確實是可折疊標頭並完成切換時為 ``True``
            / ``True`` when the line was a foldable header and the state flipped
        """
        regions = self.compute_regions()
        if region_at_line(regions, line) is None:
            return False
        if line in self._folded_headers:
            self._folded_headers.discard(line)
        else:
            self._folded_headers.add(line)
        self._reapply(regions)
        return True

    def fold_all(self) -> None:
        """折疊所有可折疊區塊 / Fold every foldable region."""
        regions = self.compute_regions()
        self._folded_headers = {region.start for region in regions}
        self._reapply(regions)

    def unfold_all(self) -> None:
        """展開所有折疊 / Unfold everything."""
        self._folded_headers.clear()
        self._reapply(self.compute_regions())

    def refresh(self) -> None:
        """
        文字變更後重新套用折疊
        Re-apply folds after the text changed.

        不再對應到有效標頭的折疊會被丟棄，其內容自然恢復可見。
        Folds that no longer match a valid header are dropped and their content
        becomes visible again.
        """
        regions = self.compute_regions()
        valid_headers = {region.start for region in regions}
        self._folded_headers &= valid_headers
        self._reapply(regions)

    def _reapply(self, regions: list[FoldRegion]) -> None:
        """
        依目前折疊狀態設定每一行的可見性
        Set every line's visibility from the current fold state.
        """
        document = self._editor.document()
        # 先讓所有行可見，確保不會殘留被錯誤隱藏的行
        # Make every line visible first so no line is left wrongly hidden
        block = document.firstBlock()
        while block.isValid():
            if not block.isVisible():
                block.setVisible(True)
            block = block.next()

        region_by_header = {region.start: region for region in regions}
        for header in sorted(self._folded_headers):
            region = region_by_header.get(header)
            if region is None:
                continue
            self._hide_region_body(document, region)

        self._relayout()

    def _hide_region_body(self, document, region: FoldRegion) -> None:
        """隱藏折疊區塊的內容行 / Hide the body lines of a folded region."""
        for line in region.body_lines:
            block = document.findBlockByNumber(line)
            if block.isValid():
                block.setVisible(False)

    def _relayout(self) -> None:
        """
        通知編輯器重新計算版面
        Ask the editor to recompute its layout after visibility changed.

        標記整份文件為 dirty 會讓 ``QPlainTextDocumentLayout`` 重新計算高度與捲軸，
        隱藏的行高度為零而自然收合。
        Marking the whole document dirty makes ``QPlainTextDocumentLayout`` recompute
        heights and scrollbars; hidden blocks have zero height and collapse away.
        """
        try:
            document = self._editor.document()
            document.markContentsDirty(0, document.characterCount())
            self._editor.update_line_number_area_width(0)
            self._editor.viewport().update()
            self._editor.line_number.update()
        except RuntimeError as error:
            # 編輯器可能在關閉過程中被銷毀 / The editor may be torn down mid-close
            jeditor_logger.warning(f"folding_manager.py relayout skipped: {error}")
