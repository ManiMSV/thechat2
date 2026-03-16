import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { ChatService } from '../../../core/chat.service';
import { AuthService } from '../../../core/auth.service';
import { Conversation } from '../../../shared/models/conversation.model';
import { User } from '../../../shared/models/user.model';

@Component({
  selector: 'app-conversation-list',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './conversation-list.component.html',
  styleUrls: ['./conversation-list.component.css'],
})
export class ConversationListComponent implements OnInit {
  conversations: Conversation[] = [];
  otherUsers: Record<string, User> = {};
  currentUserId: string | null = null;

  constructor(private chat: ChatService, private auth: AuthService) {}

  ngOnInit() {
    this.auth.currentUser$.subscribe(user => {
      this.currentUserId = user?.id ?? null;
      if (this.currentUserId) this.loadConversations();
    });
  }

  loadConversations() {
    this.chat.getConversations().subscribe(convs => {
      this.conversations = convs.sort(
        (a, b) => new Date(b.last_message_at).getTime() - new Date(a.last_message_at).getTime()
      );
      convs.forEach(conv => this.resolveOtherUser(conv));
    });
  }

  private resolveOtherUser(conv: Conversation) {
    const otherId = conv.participants.find(p => p !== this.currentUserId);
    if (!otherId) return;
    const cached = this.auth.getCachedUser(otherId);
    if (cached) {
      this.otherUsers[conv.id] = cached;
    } else {
      this.chat.getUser(otherId).pipe(catchError(() => of(null))).subscribe(u => {
        if (u) {
          this.auth.cacheUser(u);
          this.otherUsers[conv.id] = u;
        }
      });
    }
  }

  getDisplayName(conv: Conversation): string {
    const u = this.otherUsers[conv.id];
    if (u) return u.username;
    const otherId = conv.participants.find(p => p !== this.currentUserId);
    return otherId ? '…' + otherId.slice(-6) : 'Unknown';
  }

  getAvatarLetter(conv: Conversation): string {
    const u = this.otherUsers[conv.id];
    return u ? u.username[0].toUpperCase() : '?';
  }

  formatTime(dateStr: string): string {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 60_000) return 'just now';
    if (diff < 3_600_000) return Math.floor(diff / 60_000) + 'm';
    if (diff < 86_400_000) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }
}
