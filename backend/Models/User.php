<?php

namespace SalitAACo\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class User extends Model
{
    protected $table = "users";

    // created_at is filled in by MySQL (DEFAULT CURRENT_TIMESTAMP). Eloquent must
    // not write timestamps itself, so every stored time stays on the database
    // clock that the admin dashboard compares against CURDATE().
    public $timestamps = false;

    // is_admin is left out on purpose: it can only be granted directly in the database.
    protected $fillable = ["username", "password_hash", "display_name"];

    protected $hidden = ["password_hash", "avatar_data"];

    public function customizations(): HasMany
    {
        return $this->hasMany(Customization::class);
    }
}
