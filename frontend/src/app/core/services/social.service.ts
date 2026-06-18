import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UserPublic {
  user_id: string;
  username: string;
  first_name: string;
  last_name: string;
  avatar_url?: string;
}

export interface FriendshipResponse {
  friendship_id: string;
  user_id: string;
  friend_id: string;
  status: string;
  created_at: string;
  friend: UserPublic;
}

export interface ChatroomResponse {
  room_id: string;
  name?: string;
  is_group: boolean;
  created_at: string;
  members: UserPublic[];
}

export interface ChatMessageResponse {
  message_id: string;
  room_id: string;
  sender_id: string;
  content: string;
  created_at: string;
  sender: UserPublic;
}

@Injectable({
  providedIn: 'root'
})
export class SocialService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/api/v1/social';

  searchUsers(query: string): Observable<UserPublic[]> {
    return this.http.get<UserPublic[]>(`${this.apiUrl}/friends/search`, { params: { query } });
  }

  getFriends(): Observable<{ friends: FriendshipResponse[], pending_incoming: FriendshipResponse[], pending_outgoing: FriendshipResponse[] }> {
    return this.http.get<any>(`${this.apiUrl}/friends`);
  }

  sendFriendRequest(targetUserId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/friends/request/${targetUserId}`, {});
  }

  acceptFriendRequest(friendshipId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/friends/accept/${friendshipId}`, {});
  }

  declineFriendRequest(friendshipId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/friends/decline/${friendshipId}`, {});
  }

  removeFriend(friendId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/friends/${friendId}`);
  }

  getChatrooms(): Observable<ChatroomResponse[]> {
    return this.http.get<ChatroomResponse[]>(`${this.apiUrl}/chatrooms`);
  }

  getChatMessages(roomId: string, offset: number = 0, limit: number = 50): Observable<ChatMessageResponse[]> {
    return this.http.get<ChatMessageResponse[]>(`${this.apiUrl}/chatrooms/${roomId}/messages`, { params: { offset, limit } });
  }
}
