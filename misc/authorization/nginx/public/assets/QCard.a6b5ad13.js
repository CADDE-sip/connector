var f=Object.defineProperty,g=Object.defineProperties;var m=Object.getOwnPropertyDescriptors;var s=Object.getOwnPropertySymbols;var q=Object.prototype.hasOwnProperty,h=Object.prototype.propertyIsEnumerable;var u=(a,e,r)=>e in a?f(a,e,{enumerable:!0,configurable:!0,writable:!0,value:r}):a[e]=r,n=(a,e)=>{for(var r in e||(e={}))q.call(e,r)&&u(a,r,e[r]);if(s)for(var r of s(e))h.call(e,r)&&u(a,r,e[r]);return a},c=(a,e)=>g(a,m(e));import{u as F,a as v}from"./use-dark.e99ac626.js";import{c as p,h as b}from"./use-align.4d382a04.js";import{c as k,h as C,g as B}from"./index.4807e50e.js";let t=[],o=[];function d(a){o=o.filter(e=>e!==a)}function y(a){d(a),o.push(a)}function S(a){d(a),o.length===0&&t.length>0&&(t[t.length-1](),t=[])}function W(a){o.length===0?a():t.push(a)}function I(a){t=t.filter(e=>e!==a)}var P=p({name:"QCard",props:c(n({},F),{tag:{type:String,default:"div"},square:Boolean,flat:Boolean,bordered:Boolean}),setup(a,{slots:e}){const r=B(),l=v(a,r.proxy.$q),i=k(()=>"q-card"+(l.value===!0?" q-card--dark q-dark":"")+(a.bordered===!0?" q-card--bordered":"")+(a.square===!0?" q-card--square no-border-radius":"")+(a.flat===!0?" q-card--flat no-shadow":""));return()=>C(a.tag,{class:i.value},b(e.default))}});export{P as Q,W as a,S as b,y as c,I as r};
