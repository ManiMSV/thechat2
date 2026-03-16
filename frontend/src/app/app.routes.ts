import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login/login.component';
import { RegisterComponent } from './features/auth/register/register.component';
import { ChatShellComponent } from './features/chat/chat-shell/chat-shell.component';
import { ChatWindowComponent } from './features/chat/chat-window/chat-window.component';
import { authGuard } from './core/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/chat', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  {
    path: 'chat',
    component: ChatShellComponent,
    canActivate: [authGuard],
    children: [
      { path: ':id', component: ChatWindowComponent },
    ],
  },
];
