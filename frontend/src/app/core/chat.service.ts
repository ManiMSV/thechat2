import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { User } from '../shared/models/user.model';
import { Conversation } from '../shared/models/conversation.model';
import { Message } from '../shared/models/message.model';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ChatService {
  constructor(private http: HttpClient) {}

  getConversations(): Observable<Conversation[]> {
    return this.http.get<Conversation[]>(`${environment.apiBaseUrl}api/conversations`);
  }

  startConversation(participantId: string): Observable<Conversation> {
    return this.http.post<Conversation>(`${environment.apiBaseUrl}api/conversations`, { participant_id: participantId });
  }

  getMessages(conversationId: string): Observable<Message[]> {
    return this.http.get<Message[]>(`${environment.apiBaseUrl}api/conversations/${conversationId}/messages`);
  }

  sendMessage(conversationId: string, content: string): Observable<Message> {
    return this.http.post<Message>(`${environment.apiBaseUrl}api/conversations/${conversationId}/messages`, { content });
  }

  markAsRead(conversationId: string): Observable<void> {
    return this.http.post<void>(`${environment.apiBaseUrl}api/conversations/${conversationId}/messages/read`, {});
  }

  searchUsers(q: string): Observable<User[]> {
    return this.http.get<User[]>(`${environment.apiBaseUrl}api/users/search?q=${encodeURIComponent(q)}`);
  }

  getUser(userId: string): Observable<User> {
    return this.http.get<User>(`${environment.apiBaseUrl}api/users/${userId}`);
  }
}
