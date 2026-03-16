import { User } from './user.model';

export interface Conversation {
  id: string;
  participants: string[];
  created_at: string;
  last_message_at: string;
  other_user: User;
  last_message_preview: string | null;
  unread_count: number;
}
