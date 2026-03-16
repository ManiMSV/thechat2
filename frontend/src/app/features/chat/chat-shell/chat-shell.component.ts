import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { ConversationListComponent } from '../conversation-list/conversation-list.component';
import { NewChatModalComponent } from '../new-chat-modal/new-chat-modal.component';
import { AuthService } from '../../../core/auth.service';
import { User } from '../../../shared/models/user.model';

@Component({
  selector: 'app-chat-shell',
  standalone: true,
  imports: [CommonModule, ConversationListComponent, NewChatModalComponent, RouterModule],
  templateUrl: './chat-shell.component.html',
  styleUrls: ['./chat-shell.component.css'],
})
export class ChatShellComponent implements OnInit {
  showNewChat = false;
  isConversationOpen = false;
  currentUser: User | null = null;

  constructor(private auth: AuthService, private router: Router) {}

  ngOnInit() {
    this.auth.currentUser$.subscribe(u => this.currentUser = u);
    this.router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe(() => {
      this.isConversationOpen = this.router.url.includes('/chat/');
    });
    this.isConversationOpen = this.router.url.includes('/chat/');
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
