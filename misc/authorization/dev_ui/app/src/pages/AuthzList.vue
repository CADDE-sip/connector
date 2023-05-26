<template>
  <div class="q-pa-md items-start q-gutter-md">
    <q-card class="shadow-24 q-pa-lg">
      <q-table :columns="columns" :rows="rows" @row-click="onRowClick" title="認可一覧" separator="vertical" :rows-per-page-options="[0, 10]" rows-per-page-label="表示数" :pagination-label="getPaginationLabel"/>
      <q-card-actions class="q-px-lg">
        <span style="color:red">{{err_msg}}</span>
      </q-card-actions>
    </q-card>
  </div>
</template>

<script setup>
import { api } from 'boot/axios'
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from '../stores/store'
import { useQuasar } from 'quasar'

const router = useRouter()
const store = useStore()
const columns = [
  { name: 'target', label: '配信のURL', field: 'target', align: 'left' },
]
const rows = ref([])

const getPaginationLabel = (firstRowIndex, endRowIndex, totalRowsNumber) => {
  return `${totalRowsNumber}項目中${firstRowIndex}～${endRowIndex}項目を表示中`
}

let err_msg = ref('')

const fetch = () => {
  err_msg.value = ''
  api.get('/cadde/api/v4/ui/authorization_list', {})
    .then(response => {
      let data = response.data

      let targets= []
      data.forEach(function(elem, index) {
        targets.push(elem.permission.target)
      });
      const targets_nudup = Array.from(new Set(targets))

      let rows_data = []
      targets_nudup.forEach(function(elem, index) {
        let row_data = {id: index, target: elem}
        rows_data.push(row_data)
      });

      rows.value = rows_data
    })
    .catch(function (error) {
        console.log(error)
        if (error.response.status == 403) {
          err_msg.value = '有効期限切れのため認可一覧の取得ができませんでした。ログインしなおしてください。'
        } else {
          err_msg.value = 'サーバ障害のため認可一覧の取得ができませんでした。サーバの状態を確認してください。'
        }
      })
}

const onRowClick = (evt, row) => {
  router.push({name: 'detail', params: {target: row.target} })
}

fetch()

</script>

