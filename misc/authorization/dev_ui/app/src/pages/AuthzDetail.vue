<template>
  <div class="q-pa-md items-start q-gutter-md">
    <q-card class="shadow-24 q-pa-lg">
      <q-card-section>
        <div class="text-h6">配信のURL</div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <div class="text-h6">{{$route.params.target}}</div>
        <!--
        <div class="q-pa-xl q-gutter-xl">
          <q-btn @click="delete_resource" label="配信削除" color="negative" />
        </div>
        -->
      </q-card-section>
      <q-separator />
      <q-table :columns="columns" :rows="rows" title="認可" separator="vertical" selection="single" row-key="index" :rows-per-page-options="[0, 10]" rows-per-page-label="表示数" :selected-rows-label="getSelectedString" v-model:selected="selected" :pagination-label="getPaginationLabel"/>
      <q-card-actions class="q-px-md">
        <div v-show="selected.length != 0" class="q-pa-md">
          <q-btn @click="delete_authorization" label="認可削除" color="negative" />
        </div>
      </q-card-actions>
      <q-card-actions class="q-px-lg">
        <span style="color:red">{{get_err_msg}}</span>
        <span style="color:red">{{delete_err_msg}}</span>
      </q-card-actions>
    </q-card>
  </div>
</template>

<script setup>
import { api } from 'boot/axios'
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from '../stores/store'

const router = useRouter()
const route = useRoute()
const store = useStore()

const columns = [
  { name: 'user', label: 'ユーザ', field: 'user', align: 'left' },
  { name: 'org', label: '組織', field: 'org', align: 'left' },
  { name: 'aal', label: 'AAL', field: 'aal', align: 'left' },
  { name: 'trade_id', label: '取引ID', field: 'trade_id', align: 'left' }
]
const rows = ref([])
const selected = ref([])
const target = route.params.target

const getSelectedString = (numberOfRows) => {
  return ""
}

const getPaginationLabel = (firstRowIndex, endRowIndex, totalRowsNumber) => {
  return `${totalRowsNumber}項目中${firstRowIndex}～${endRowIndex}項目を表示中`
}

let get_err_msg = ref('')
let delete_err_msg = ref('')

const fetch = () => {
  get_err_msg.value = ''
  api.get("/cadde/api/v4/ui/authorization", {
    params: {
      target: target
    }})
    .then(response => {
      let data = response.data
      let rows_data = []
      data.forEach(function(elem, index) {
        let row_data = null
        if ("contract" in elem) {
          row_data = {index: index, user: elem.permission.assignee.user, org: elem.permission.assignee.org, aal: elem.permission.assignee.aal, trade_id: elem.contract.trade_id}
        } else {
          row_data = {index: index, user: elem.permission.assignee.user, org: elem.permission.assignee.org, aal: elem.permission.assignee.aal, trade_id: null}
        }
        rows_data.push(row_data)
      })
      rows.value = rows_data
    })
    .catch(function (error) {
      console.log(error)
      if (error.response.status == 403) {
        get_err_msg.value = '有効期限切れのため認可詳細の取得ができませんでした。ログインしなおしてください。'
      } else {
        get_err_msg.value = 'サーバ障害のため認可詳細の取得ができませんでした。サーバの状態を確認してください。'
      }
    })
}

const delete_authorization = () => {

  let authorization_to_delete = {}
  delete_err_msg.value = ''

  if (selected.value[0].trade_id != null) {

    authorization_to_delete = {
      "permission": {
        "target": route.params.target,
         "assigner": store.cadde_user_id
      },
      "contract": {
        "trade_id": selected.value[0].trade_id
      }
    }

  } else {

    if (typeof selected.value[0].user === "undefined") {
      selected.value[0].user = null
    }
    if (typeof selected.value[0].org === "undefined") {
      selected.value[0].org = null
    }
    if (typeof selected.value[0].aal === "undefined") {
      selected.value[0].aal = null
    }

    authorization_to_delete = {
      "permission": {
        "target": route.params.target,
        "assigner": store.cadde_user_id,
        "assignee": {
          "user": selected.value[0].user,
          "org": selected.value[0].org,
          "aal": selected.value[0].aal,
          "extras": null
        }
      }
    }

  }

  api.delete("/cadde/api/v4/ui/authorization", {
     data: authorization_to_delete
    })
    .then(function (response) {
      fetch()
    })
    .catch(function (error) {
      console.log(error)
      if (error.response.status == 403) {
        delete_err_msg.value = '有効期限切れのため認可削除ができませんでした。ログインしなおしてください。'
      } else if (error.response.status == 404) {
        delete_err_msg.value = ''
      } else {
        delete_err_msg.value = 'サーバ障害のため認可削除ができませんでした。サーバの状態を確認してください。'
      }
    })
}

fetch()

</script>
