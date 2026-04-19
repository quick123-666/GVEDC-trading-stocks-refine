const config = require('../../config/routing.yml');

console.log('路由服务启动...');
console.log('路由规则:', config.rules);

// 实现路由逻辑
function routeQuery(query) {
  // 根据查询类型和规则路由到相应的数据库
  for (const rule of config.rules) {
    if (new RegExp(rule.pattern).test(query)) {
      console.log(`路由查询到: ${rule.target}`);
      return rule.target;
    }
  }
  return 'relational'; // 默认路由到关系型数据库
}

// 模拟路由操作
setInterval(() => {
  console.log('执行查询路由...');
  // 实现路由操作
}, 30000);

console.log('路由服务运行中...');