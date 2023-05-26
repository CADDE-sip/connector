<template>
  <div class="q-pa-md items-start q-gutter-md">
    <q-card class="shadow-24 q-pa-lg">
      <q-card-section>
        <div class="text-h6">認可機能の設定</div>
      </q-card-section>
      <q-separator />
      <q-list bordered separator>
        <q-item>
          <q-item-section side>
            <q-item-label>アクセストークン生存期間(秒)</q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-input v-model="realm_settings.access_token_lifespan" type="text" label="アクセストークン生存期間(秒)" />
          </q-item-section>
          <q-item-section side>
            <q-btn @click="update_realm_settings" label="アクセストークン生存期間更新" color="primary" />
          </q-item-section>
        </q-item>
      </q-list>
      <q-card-actions class="q-px-lg">
        <span style="color:red">{{token_err_msg}}</span>
      </q-card-actions>
    </q-card>

    <q-card class="shadow-24 q-pa-lg">
      <q-card-section>
        <div class="text-h6">提供者コネクタ設定</div>
      </q-card-section>
      <q-separator />
      <q-item>
        <q-item-section side>クライアントID(提供者コネクタURL)</q-item-section>
        <q-item-section side>{{ client_settings.client_id }}</q-item-section>
      </q-item>
      <q-item>
        <q-item-section side>提供者コネクタクライアントシークレット</q-item-section>
        <q-item-section side>{{ client_settings.client_secret }}</q-item-section>
        <q-item-section side>
          <q-btn @click="update_client_secret" label="クライアントシークレット更新" color="primary" />
        </q-item-section>
      </q-item>
      <q-card-actions class="q-px-lg">
        <span style="color:red">{{client_err_msg}}</span>
      </q-card-actions>
    </q-card>

    <q-card class="shadow-24 q-pa-lg">
      <q-card-section>
        <div class="text-h6">認証機能との連携設定</div>
      </q-card-section>
      <q-separator />
      <q-input v-model="idp_settings.userinfo_url" type="text" label="UserInfo URL"
        :rules="[val => /^[a-zA-Z0-9!-/:-@¥[-`{-~]*$/.test(val) || '使用可能文字のみを入力してください']">
      </q-input>
      <div class="q-pa-xl q-gutter-xl">
        <q-btn @click="update_idp_settings" label="認証機能との連携設定更新" color="primary" />
      </div>
      <q-card-actions class="q-px-lg">
        <span style="color:red">{{idp_err_msg}}</span>
      </q-card-actions>
    </q-card>

  </div>
</template>

<script setup>
import { api } from 'boot/axios'
import { ref, reactive, onUpdated, onBeforeMount, onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from '../stores/store'

const router = useRouter()
const store = useStore()

const realm_settings = ref({})
const client_settings = ref({})
const idp_settings = ref({})

let token_err_msg = ref('')
let client_err_msg = ref('')
let idp_err_msg = ref('')


const fetch = () => {
  token_err_msg.value = ''
  client_err_msg.value = ''
  idp_err_msg.value = ''
  api.get('/cadde/api/v4/ui/settings')
    .then(response => {
      realm_settings.value = response.data.realm_settings
      client_settings.value = response.data.client_settings
      idp_settings.value = response.data.idp_settings
    })
    .catch(function (error) {
      console.log(error)
      if (error.response.status == 403) {
        token_err_msg.value = '有効期限切れのためアクセストークン生存期間の取得ができませんでした。ログインしなおしてください。'
        client_err_msg.value = '有効期限切れのためクライアントシークレットの取得ができませんでした。ログインしなおしてください。'
        idp_err_msg.value = '有効期限切れのためUserInfo URLの取得ができませんでした。ログインしなおしてください。'
      } else{
        token_err_msg.value = 'サーバ障害のためアクセストークン生存期間の取得ができませんでした。サーバの状態を確認してください。'
        client_err_msg.value = 'サーバ障害のためクライアントシークレットの取得ができませんでした。サーバの状態を確認してください。'
        idp_err_msg.value = 'サーバ障害のためUserInfo URLの取得ができませんでした。サーバの状態を確認してください。'
      }
    })
}

const update_realm_settings = () => {
  token_err_msg.value = ''
  console.log(realm_settings.value.access_token_lifespan)
  console.log(typeof realm_settings.value.access_token_lifespan)
  if (isNaN(realm_settings.value.access_token_lifespan)) {
    token_err_msg.value = '数字を入力してください'
  } else if(realm_settings.value.access_token_lifespan < 0){
    token_err_msg.value = '正の数を入力してください'
  } else{
    api.put('/cadde/api/v4/ui/settings/realm', realm_settings.value)
      .then(response => {
        fetch()
      })
      .catch(function (error) {
        console.log(error)
        if (error.response.status == 403) {
          token_err_msg.value = '有効期限切れのためアクセストークン生存期間の更新ができませんでした。ログインしなおしてください。'
        } else{
          token_err_msg.value = 'サーバ障害のためアクセストークン生存期間の更新ができませんでした。サーバの状態を確認してください。'
        }        
      })
  }
}

const update_client_secret = () => {
  client_err_msg.value = ''
  api.put(`/cadde/api/v4/ui/settings/client_secret`)
    .then(response => {
      fetch()
    })
    .catch(function (error) {
      console.log(error)
      if (error.response.status == 403) {
        client_err_msg.value = '有効期限切れのためクライアントシークレットの更新ができませんでした。ログインしなおしてください。'
      } else {
        client_err_msg.value = 'サーバ障害のためクライアントシークレットの更新ができませんでした。サーバの状態を確認してください。'
      }
    })
}

const update_idp_settings = () => {
  idp_err_msg.value = ''
  api.put("/cadde/api/v4/ui/settings/idp", idp_settings.value)
    .then(response => {
      fetch()
    })
    .catch(function (error) {
      console.log(error)
      if (error.response.status == 403) {
        idp_err_msg.value = '有効期限切れのためUserInfo URLの更新ができませんでした。ログインしなおしてください。'
      } else {
        idp_err_msg.value = 'サーバ障害のためUserInfo URLの更新ができませんでした。サーバの状態を確認してください。'
      }
    })
}

fetch()

</script>
