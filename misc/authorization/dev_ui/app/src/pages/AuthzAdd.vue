<template>
  <div class="q-pa-md items-start q-gutter-md">
    <q-card square class="shadow-24 q-pa-lg">
      <div class="q-px-md text-h6">認可登録</div>
      <q-form>
        <q-card-section>
          <q-input ref="urlval" v-model="authz.permission.target" type="text" lazy-rules label="認可の対象とするURL（最大文字数は255字以内）"
            :rules="[val => !!val || 'Field is required', val => val.length <= 255 || '255文字以内で入力してください', val => /^[a-zA-Z0-9!-/:-@¥[-`{-~]*$/.test(val) || '使用可能文字のみを入力してください']">
          </q-input>
        </q-card-section>
        <q-card-section>
          <q-toggle v-model="user_enabled" label="ユーザに対する認可" />
          <div v-show="user_enabled">
            <q-input v-model="authz.permission.assignee.user" type="text" lazy-rules label="ユーザのCADDEユーザID"
              :rules="[val => val.length <= 255 || '255文字以内で入力してください']">
            </q-input>
          </div>
        </q-card-section>
        <q-card-section>
          <q-toggle v-model="org_enabled" label="組織に対する認可" />
          <div v-show="org_enabled">
            <q-input v-model="authz.permission.assignee.org" type="text" lazy-rules label="組織のCADDEユーザID"
              :rules="[val => val.length <= 255 || '255文字以内で入力してください']">
            </q-input>
          </div>
        </q-card-section>
        <q-card-section>
          <q-toggle v-model="aal_enabled" label="当人認証レベルに対する認可" />
          <div v-if="aal_enabled" class="q-pa-md">
            <q-btn-toggle v-model="authz.permission.assignee.aal" toggle-color="primary" :options="[
            {label: '1', value: 1},
            {label: '2', value: 2},
            {label: '3', value: 3}
            ]" />
          </div>
        </q-card-section>
        <q-card-actions class="q-px-md">
          <div v-show="isVisible()" class="q-pa-md">
            <q-btn @click="register" color="primary" label="認可設定" />
          </div>
        </q-card-actions>
        <q-card-actions class="q-px-lg">
          <span style="color:red">{{err_msg}}</span>
        </q-card-actions>
      </q-form>
    </q-card>
  </div>
</template>

<script setup>
import { api } from 'boot/axios'
import { ref, onUpdated, onBeforeMount, onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from '../stores/store'
import { useQuasar } from 'quasar'

const router = useRouter()
const store = useStore()

const user_enabled = ref(false)
const org_enabled = ref(false)
const aal_enabled = ref(false)

const authz = ref({
  permission: {
    target: null,
    assigner: store.cadde_user_id,
    assignee: {
      user: null,
      org: null,
      aal: null,
      extras: null
    }
  }
})

let err_msg = ref('')

const isVisible = () => {
 return authz.value.permission.target != null && authz.value.permission.target != "" && ((user_enabled.value && authz.value.permission.assignee.user != null && authz.value.permission.assignee.user != "") || (org_enabled.value && authz.value.permission.assignee.org != null && authz.value.permission.assignee.org != "") || (aal_enabled.value && authz.value.permission.assignee.aal != null && authz.value.permission.assignee.aal != ""))
}

const register = () => {

  err_msg.value = ''

  // トグルボタンをONにしていなかったり、空文字だった場合は、NULLにする
  if (user_enabled.value == false || authz.value.permission.assignee.user == "") {
    authz.value.permission.assignee.user = null
  }
  if (org_enabled.value == false || authz.value.permission.assignee.org == "") {
    authz.value.permission.assignee.org = null
  }
  if (aal_enabled.value == false || authz.value.permission.assignee.aal == "") {
    authz.value.permission.assignee.aal = null
  }

  // バリデーションチェックで問題なければ認可登録リクエスト送信
  if (authz.value.permission.target == null || authz.value.permission.target == "") {
    err_msg.value = '配信のURLを入力してください'
  } else if (authz.value.permission.target.length >= 255){
    err_msg.value = '配信のURLは255文字以内で入力してください'
  } else if (authz.value.permission.assignee.user == null && authz.value.permission.assignee.org == null && authz.value.permission.assignee.aal == null) {
    err_msg.value = '少なくともひとつの認可の条件を指定してください'
  } else {
    api.post("/cadde/api/v4/ui/authorization", authz.value)
      .then(function (response) {
        err_msg.value = '認可を設定しました'
      })
      .catch(function (error) {
        console.log(error)
        if (error.response.status == 403) {
          err_msg.value = '有効期限切れのため認可登録ができませんでした。ログインしなおしてください。'
        } else {
          err_msg.value = 'サーバ障害のため認可登録ができませんでした。サーバの状態を確認してください。'
        }
      })
  }
}

</script>
