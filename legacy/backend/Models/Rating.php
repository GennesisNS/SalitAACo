<?php

namespace SalitAACo\Models;

use Illuminate\Database\Eloquent\Model;

// One rating per user (app rating + optional comment).
class Rating extends Model
{
    protected $table = "ratings";

    // created_at / updated_at are maintained by MySQL column defaults.
    public $timestamps = false;
}
