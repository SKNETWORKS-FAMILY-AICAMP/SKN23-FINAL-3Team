import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/theme/app_colors.dart';
import '../../shared/models/app_notification.dart';
import 'notification_provider.dart';

class NotificationSheet extends ConsumerWidget {
  const NotificationSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationProvider);
    final unread = ref.watch(unreadCountProvider);

    return DraggableScrollableSheet(
      initialChildSize: 0.65,
      minChildSize: 0.4,
      maxChildSize: 0.92,
      expand: false,
      builder: (_, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // 핸들 바
              Container(
                margin: const EdgeInsets.only(top: 10, bottom: 4),
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              // 헤더
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 12, 8),
                child: Row(
                  children: [
                    const Icon(
                      LucideIcons.bell,
                      color: AppColors.brandOrange,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '알림${unread > 0 ? ' ($unread)' : ''}',
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.bold,
                          color: AppColors.darkBrown,
                        ),
                      ),
                    ),
                    if (unread > 0)
                      TextButton(
                        onPressed: () =>
                            ref.read(notificationProvider.notifier).markAllRead(),
                        child: const Text(
                          '모두 읽음',
                          style: TextStyle(
                            fontSize: 12,
                            color: AppColors.brandOrange,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    if (notifications.isNotEmpty)
                      IconButton(
                        icon: const Icon(LucideIcons.trash2, size: 16),
                        color: AppColors.mutedForeground,
                        tooltip: '전체 삭제',
                        onPressed: () {
                          ref.read(notificationProvider.notifier).clear();
                        },
                      ),
                  ],
                ),
              ),
              const Divider(height: 1, color: Color(0xFFF3E4D3)),
              // 알림 목록
              Expanded(
                child: notifications.isEmpty
                    ? const _EmptyState()
                    : ListView.separated(
                        controller: scrollController,
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                        itemCount: notifications.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 8),
                        itemBuilder: (_, i) {
                          return _NotificationCard(
                            notification: notifications[i],
                            onTap: () {
                              ref
                                  .read(notificationProvider.notifier)
                                  .markRead(notifications[i].id);
                            },
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            LucideIcons.bellOff,
            size: 48,
            color: AppColors.beige,
          ),
          SizedBox(height: 12),
          Text(
            '알림이 없어요',
            style: TextStyle(
              fontSize: 14,
              color: AppColors.mutedForeground,
              fontWeight: FontWeight.w500,
            ),
          ),
          SizedBox(height: 4),
          Text(
            '새로운 알림이 생기면 여기에 표시돼요',
            style: TextStyle(
              fontSize: 12,
              color: AppColors.mutedForeground,
            ),
          ),
        ],
      ),
    );
  }
}

class _NotificationCard extends StatelessWidget {
  const _NotificationCard({
    required this.notification,
    required this.onTap,
  });

  final AppNotification notification;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isUnread = !notification.isRead;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: isUnread ? const Color(0xFFFFF5EE) : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isUnread
                ? AppColors.brandOrange.withOpacity(0.25)
                : const Color(0xFFF3E4D3),
          ),
          boxShadow: isUnread
              ? [
                  BoxShadow(
                    color: AppColors.brandOrange.withOpacity(0.06),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 아이콘
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: isUnread ? AppColors.peach : const Color(0xFFF5F0EB),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Center(
                child: Icon(
                  _iconForType(notification.type),
                  size: 18,
                  color: isUnread
                      ? AppColors.brandOrange
                      : AppColors.mutedForeground,
                ),
              ),
            ),
            const SizedBox(width: 12),
            // 내용
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          notification.title,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight:
                                isUnread ? FontWeight.bold : FontWeight.w500,
                            color: AppColors.darkBrown,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _formatTime(notification.createdAt),
                        style: const TextStyle(
                          fontSize: 10,
                          color: AppColors.mutedForeground,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(
                    notification.body,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.subBrown2,
                      height: 1.4,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            // 읽지 않은 표시
            if (isUnread) ...[
              const SizedBox(width: 6),
              Container(
                width: 8,
                height: 8,
                margin: const EdgeInsets.only(top: 4),
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.brandOrange,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  static IconData _iconForType(NotificationType type) {
    return switch (type) {
      NotificationType.diaryReminder => LucideIcons.pencil,
      NotificationType.diarySaved => LucideIcons.bookOpen,
      NotificationType.imageGenerated => LucideIcons.image,
      NotificationType.favoriteAdded => LucideIcons.star,
      NotificationType.photoStyleDone => LucideIcons.palette,
    };
  }

  static String _formatTime(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);

    if (diff.inMinutes < 1) return '방금 전';
    if (diff.inMinutes < 60) return '${diff.inMinutes}분 전';
    if (diff.inHours < 24) return '${diff.inHours}시간 전';
    if (diff.inDays < 7) return '${diff.inDays}일 전';
    return '${dt.month}/${dt.day}';
  }
}
