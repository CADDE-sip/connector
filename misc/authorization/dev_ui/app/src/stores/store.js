import { defineStore } from 'pinia';

export const useStore = defineStore('store', {
  state: () => ({
    authInfo: {
      keycloakState: "",
      keycloakCode: ""
    },
    cadde_user_id: "",
  }),
  getters: {
  },
  actions: {
    updateLoginInfo(obj) {
      this.cadde_user_id = obj.cadde_user_id
    },
    updateAuthInfo(getMes) {
      this.authInfo.keycloakState = getMes.keycloakState
      this.authInfo.keycloakCode =  getMes.keycloakCode
    },
  },
});
