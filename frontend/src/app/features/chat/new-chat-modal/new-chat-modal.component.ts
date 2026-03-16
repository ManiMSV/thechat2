import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ChatService } from '../../../core/chat.service';
import { AuthService } from '../../../core/auth.service';
import { User } from '../../../shared/models/user.model';

@Component({
  selector: 'app-new-chat-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './new-chat-modal.component.html',
  styleUrls: ['./new-chat-modal.component.css'],
})
export class NewChatModalComponent {
  @Output() closed = new EventEmitter<void>();

  query = '';
  results: User[] = [];
  loading = false;
  error = '';
  searched = false;

  constructor(private chat: ChatService, private auth: AuthService, private router: Router) {}

  search() {
    if (!this.query.trim()) return;
    this.loading = true;
    this.error = '';
    this.searched = true;
    this.chat.searchUsers(this.query.trim()).subscribe({
      next: (users) => {
        const myId = this.auth.getCurrentUserId();
        this.results = users.filter(u => u.id !== myId);
        users.forEach(u => this.auth.cacheUser(u));
        this.loading = false;
      },
      error: () => {
        this.error = 'Search failed. Please try again.';
        this.loading = false;
      },
    });
  }

  startChat(user: User) {
    this.auth.cacheUser(user);
    this.chat.startConversation(user.id).subscribe(conv => {
      this.closed.emit();
      this.router.navigate(['/chat', conv.id]);
    });
  }

  close() {
    this.closed.emit();
  }
}
