import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class WebsocketService {
  private socket: WebSocket | null = null;
  private messages$ = new Subject<any>();
  private conversationId: string | null = null;
  private token: string | null = null;
  private reconnectDelay = 1000;
  private readonly maxReconnectDelay = 30000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  connect(conversationId: string, token: string) {
    this.intentionalClose = false;
    this.conversationId = conversationId;
    this.token = token;
    this.reconnectDelay = 1000;
    this._openSocket();
  }

  private _openSocket() {
    if (this.socket) {
      this.socket.onclose = null;
      this.socket.close();
      this.socket = null;
    }
    const baseUrl = environment.apiBaseUrl || `${window.location.protocol}//${window.location.host}`;
    const wsUrl = baseUrl.replace(/^http/, 'ws');
    this.socket = new WebSocket(
      `${wsUrl}/ws/${this.conversationId}?token=${this.token}`
    );
    this.socket.onmessage = event => {
      try { this.messages$.next(JSON.parse(event.data)); } catch {}
    };
    this.socket.onclose = () => {
      if (!this.intentionalClose) {
        this._scheduleReconnect();
      }
    };
  }

  private _scheduleReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      if (!this.intentionalClose && this.conversationId && this.token) {
        this._openSocket();
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
      }
    }, this.reconnectDelay);
  }

  send(content: string) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: 'message', content }));
    }
  }

  onMessage(): Observable<any> {
    return this.messages$.asObservable();
  }

  close() {
    this.intentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.conversationId = null;
    this.token = null;
  }
}
