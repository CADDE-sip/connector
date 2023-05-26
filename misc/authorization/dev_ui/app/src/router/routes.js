import { useStore } from '../stores/store'

const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '/', component: () => import('pages/RedirectPage.vue') },
      {
        path: '/logout',
        beforeEnter(to, from, next) { window.location = to.query.logoutUrl }
      },
      { 
        path: '/load',
        component: () => import('pages/LoginPage.vue'),
        beforeEnter(to, from, next) {
          var store = useStore()
          store.updateAuthInfo({
            keycloakState: to.query.state,
            keycloakCode: to.query.code
          })
          next()
        },
      },
      { path: '/keycloak', name: 'keycloak', beforeEnter(to, from, next) { window.location = to.query.keycloakUrl } },
      { path: '/login', component: () => import('pages/LoginPage.vue') },
      { path: '/settings', component: () => import('pages/BasicSettings.vue'), meta: { requireAuth: true } },
      { path: '/list', component: () => import('pages/AuthzList.vue'), meta: { requireAuth: true } },
      { path: '/register', component: () => import('pages/AuthzAdd.vue'), meta: { requireAuth: true } },
      { path: '/detail', name: 'detail', component: () => import('pages/AuthzDetail.vue'), meta: { requireAuth: true } }
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
