import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import { ChatService } from '../../../core/chat.service';
import { WebsocketService } from '../../../core/websocket.service';
import { AuthService } from '../../../core/auth.service';
import { Message } from '../../../shared/models/message.model';

@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-window.component.html',
  styleUrls: ['./chat-window.component.css'],
})
export class ChatWindowComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesEnd') private messagesEnd!: ElementRef;

  conversationId: string | null = null;
  messages: Message[] = [];
  input = '';
  currentUserId: string | null = null;
  private shouldScrollToBottom = false;
  private routeSub!: Subscription;
  private wsSub!: Subscription;

  constructor(
    private route: ActivatedRoute,
    private chat: ChatService,
    private ws: WebsocketService,
    private auth: AuthService
  ) {}

  ngOnInit() {
    this.currentUserId = this.auth.getCurrentUserId();
    this.routeSub = this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id && id !== this.conversationId) {
        this.conversationId = id;
        this.messages = [];
        console.log('Loading conversation', id);
        this.ws.close();
        console.log('Loading conversation', id);
        if (this.wsSub) this.wsSub.unsubscribe();
        this.loadHistory(id);
        this.ws.connect(id, this.auth.getToken()!);
        this.wsSub = this.ws.onMessage().subscribe(msg => {
          this.messages.push(msg);
          this.shouldScrollToBottom = true;
        });
      }
    });
  }

  ngAfterViewChecked() {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  ngOnDestroy() {
    if (this.routeSub) this.routeSub.unsubscribe();
    if (this.wsSub) this.wsSub.unsubscribe();
    this.ws.close();
  }

  loadHistory(id: string) {
    this.chat.getMessages(id).subscribe((list: Message[]) => {
      this.messages = list;
      this.shouldScrollToBottom = true;
    });
  }

  send() {
    if (!this.input.trim() || !this.conversationId) return;
    this.ws.send(this.input);
    this.input = '';
  }

  isMine(msg: Message): boolean {
    return msg.sender_id === this.currentUserId;
  }

  formatTime(dateStr: string): string {
    return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  private scrollToBottom() {
    try { this.messagesEnd?.nativeElement.scrollIntoView({ behavior: 'smooth' }); } catch {}
  }
}
