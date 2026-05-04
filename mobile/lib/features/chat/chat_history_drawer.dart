import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/api/dio_error_format.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/models/chat.dart';
import 'chat_providers.dart';

/// 좌측 슬라이드 Drawer — React `ChatHistory.tsx` 1:1.
/// `Scaffold.drawer` 자동 — AppBar 햄버거 + 좌측 swipe 진입.
class ChatHistoryDrawer extends ConsumerWidget {
  const ChatHistoryDrawer({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rooms = ref.watch(chatRoomsProvider);
    final currentRoomId = ref.watch(chatProvider).chatRoomId;
    return Drawer(
      child: SafeArea(
        child: Column(
          children: [
            const _DrawerHeader(),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: FilledButton.icon(
                onPressed: () {
                  ref.read(chatProvider.notifier).resetForNewRoom();
                  Navigator.of(context).pop();
                },
                icon: const Icon(LucideIcons.plus, size: 16),
                label: const Text('새 채팅'),
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: rooms.when(
                data: (list) => list.isEmpty
                    ? const _EmptyView()
                    : ListView.builder(
                        itemCount: list.length,
                        itemBuilder: (_, i) => _RoomTile(
                          room: list[i],
                          selected: list[i].id == currentRoomId,
                        ),
                      ),
                loading: () =>
                    const Center(child: CircularProgressIndicator()),
                error: (e, _) => Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    '목록 로드 실패: $e',
                    style: const TextStyle(color: AppColors.destructive),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DrawerHeader extends StatelessWidget {
  const _DrawerHeader();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 12),
      width: double.infinity,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.gradientPeachStart, AppColors.gradientPeachEnd],
        ),
      ),
      child: const Row(
        children: [
          Icon(LucideIcons.messageCircle, color: AppColors.brandOrange),
          SizedBox(width: 8),
          Text(
            '채팅방',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppColors.darkBrown,
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyView extends StatelessWidget {
  const _EmptyView();

  @override
  Widget build(BuildContext context) {
    // R3 Empty placeholder — chatbot_logo (chat 영역 우선순위 1).
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Opacity(
            opacity: 0.4,
            child: Image.asset(
              'assets/chatbot_logo.png',
              width: 64,
              height: 64,
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            '아직 채팅 기록이 없어요.\n새 채팅을 시작해보세요.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.mutedForeground),
          ),
        ],
      ),
    );
  }
}

class _RoomTile extends ConsumerWidget {
  const _RoomTile({required this.room, required this.selected});

  final ChatRoom room;
  final bool selected;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListTile(
      selected: selected,
      selectedTileColor: AppColors.peach.withValues(alpha: 0.5),
      title: Text(
        room.title?.trim().isNotEmpty == true
            ? room.title!
            : '제목 없는 채팅',
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Text(
        _formatDate(room.updatedAt),
        style: const TextStyle(fontSize: 11),
      ),
      trailing: PopupMenuButton<_RoomMenuAction>(
        icon: const Icon(LucideIcons.moreVertical, size: 18),
        onSelected: (action) => _onMenuSelected(context, ref, action),
        itemBuilder: (_) => const [
          PopupMenuItem(
            value: _RoomMenuAction.rename,
            child: Text('이름 변경'),
          ),
          PopupMenuItem(
            value: _RoomMenuAction.delete,
            child: Text('삭제'),
          ),
        ],
      ),
      onTap: () {
        ref.read(chatProvider.notifier).openRoom(room.id);
        Navigator.of(context).pop();
      },
    );
  }

  Future<void> _onMenuSelected(
    BuildContext context,
    WidgetRef ref,
    _RoomMenuAction action,
  ) async {
    switch (action) {
      case _RoomMenuAction.rename:
        await _promptRename(context, ref);
        break;
      case _RoomMenuAction.delete:
        await _confirmDelete(context, ref);
        break;
    }
  }

  Future<void> _promptRename(BuildContext context, WidgetRef ref) async {
    final controller = TextEditingController(text: room.title ?? '');
    final newTitle = await showDialog<String>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('채팅방 이름 변경'),
        content: TextField(
          controller: controller,
          maxLength: 200,
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () =>
                Navigator.of(context).pop(controller.text.trim()),
            child: const Text('변경'),
          ),
        ],
      ),
    );
    if (newTitle == null || newTitle.isEmpty) return;
    try {
      await ref.read(chatProvider.notifier).renameRoom(room.id, newTitle);
    } catch (e) {
      Fluttertoast.showToast(msg: formatDioError(e, '이름 변경 실패'));
    }
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('채팅방 삭제'),
        content: Text('"${room.title ?? '제목 없는 채팅'}" 채팅방을 삭제할까요?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('취소'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.destructive),
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await ref.read(chatProvider.notifier).deleteRoom(room.id);
    } catch (e) {
      Fluttertoast.showToast(msg: formatDioError(e, '삭제 실패'));
    }
  }

  static String _formatDate(DateTime d) {
    final now = DateTime.now();
    if (d.year == now.year && d.month == now.month && d.day == now.day) {
      return '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
    }
    return '${d.month}/${d.day}';
  }
}

enum _RoomMenuAction { rename, delete }
