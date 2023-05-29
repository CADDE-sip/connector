<template>
  <q-page class="row justify-center items-center" style="background: linear-gradient(#f2f2f3, #f3f3f5);">
    <!--        <q-card square class="shadow-24 q-pa-lg" style="width:500px;height:400px;">
            <q-form>
                <q-card-section>
                    <q-input v-model="login_data.user_id" type="text" label="CADDEユーザID">
                    <template v-slot:prepend>
                        <q-icon name="person" />
                    </template>
                    </q-input>
                </q-card-section>
                <q-card-section>
                    <q-input v-model="login_data.password" type="password" label="パスワード">
                    <template v-slot:prepend>
                        <q-icon name="lock" />
                    </template>
                    </q-input>
                </q-card-section>
                <q-card-section>
                    <q-input v-model="login_data.totp" type="password" label="ワンタイムパスワード">
                    <template v-slot:prepend>
                        <q-icon name="phonelink_lock" />
                    </template>
                    </q-input>
                </q-card-section>
                <q-card-actions class="q-px-lg">
                    <q-btn unelevated size="lg" color="primary" @click="login" class="full-width text-white" label="ログイン" />
                </q-card-actions>
                <q-card-actions class="q-px-lg">
                  <span style="color:red">{{err_msg}}</span>
                </q-card-actions>
            </q-form>
        </q-card> -->
    <q-card-actions class="q-px-lg">
      <span style="color:red">{{ err_msg }}</span>
    </q-card-actions>
  </q-page>
</template>

<script setup>
import axios from 'axios'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from '../stores/store'
const router = useRouter()
const store = useStore()

const login_data = ref({
  client_id: "",
  user_id: "",
  password: "",
  totp: ""
})
let err_msg = ref('')

async function login() {
  err_msg.value = 'ログイン処理中...'
  let url = '/cadde/api/v4/ui/token/authorizationCode'
  let postUrl = window.location.href.split("#")
  var postData = {
    "code": store.authInfo.keycloakCode,
    "state": store.authInfo.keycloakState,
    "url": postUrl[0] + "#/"
  }
  try {
    const res = await axios.post(url, postData)
    if (res.status >= 200 && res.status < 300) {
      let obj = {}
      obj.cadde_user_id = res.data.cadde_user_id
      store.updateLoginInfo(obj)
      err_msg.value = 'ログインに成功しました'
    } else {
      console.log('login failed', res.status)
      err_msg.value = 'ログインに失敗しました'
      store.updateAuthInfo({
        keycloakState: '',
        keycloakCode: ''
      })
      router.push({ path: '/logout', query: { logoutUrl: postUrl[0] + "#/" } })
    }
  } catch (error) {
    const { status, statusText } = error.response
    console.log(error.response)
    console.log(`Error! HTTP Status: ${status} ${statusText}`)
    let msg = ''
    if (error.response.data && error.response.data.error) {
      msg = error.response.data.error
    }
    if (error.response.data && error.response.data.message) {
      msg = error.response.data.message
    }
    err_msg.value = 'ログインに失敗しました。(' + status + ':' + msg + ')'
    store.updateAuthInfo({
      keycloakState: '',
      keycloakCode: ''
    })
    router.push({ path: '/logout', query: { logoutUrl: postUrl[0] + "#/" } })
  }
}

onMounted(() => {
  login()
});

</script>
