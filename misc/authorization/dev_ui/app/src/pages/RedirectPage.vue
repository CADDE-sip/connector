<template>
  <q-layout view="lHh Lpr fff">
    <q-page class="row justify-center items-center" style="background: linear-gradient(#f2f2f3, #f3f3f5);">
      <q-card square class="shadow-24 q-pa-lg" style="width:500px;height:100px;">
        <q-form>
          <q-card-actions class="q-px-lg">
            <q-btn unelevated size="lg" color="primary" @click="clickLogin()" class="full-width text-white"
              label="ログイン" />
          </q-card-actions>
          <q-card-actions class="q-px-lg">
            <span style="color:red">{{ err_msg }}</span>
          </q-card-actions>
        </q-form>
      </q-card>
    </q-page>
  </q-layout>
</template>

<script>
import axios from 'axios'
import { ref, onBeforeMount, onUpdated, onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from '../stores/store'
import { useQuasar } from 'quasar'

export default {
  setup() {
    const router = useRouter()
    const store = useStore()
    const provider_id = ref(null)
    const provider_secret = ref(null)
    const $q = useQuasar()
    let err_msg = ref('')

    // ログインボタン押下時処理
    async function login() {
      // 認可コード取得用URLの作成
      let url = '/cadde/api/v4/ui/authenticationUrl'
      var postData = { "url": window.location.href }
      try {
        const res = await axios.post(url, postData, { headers: { 'content-type': 'application/json' } })
        if (res.status >= 200 && res.status < 300) {
          var keycloakRedirectUrl = res.data.url
          // 認可コード取得
          //console.log('keycloakログイン画面URL：%s', keycloakRedirectUrl)
          router.push({ path: '/keycloak', query: { keycloakUrl: keycloakRedirectUrl } })
        } else {
          console.log('authentication request failed', res.status)
        }
      } catch (error) {
        const { status, statusText } = error.response
        console.log(error.response)
        console.log(`Error! HTTP Status: ${status} ${statusText}`)
      }
    }

    // ログインボタン押下時処理
    function clickLogin() {
      login()
    }

    return {
      router,
      clickLogin,
      err_msg
    }
  }
}
</script>
